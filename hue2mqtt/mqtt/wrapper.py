"""MQTT Wrapper."""

import asyncio
import logging
from json import dumps
from typing import Any, Callable, Coroutine, Dict, List, Match, Optional

import gmqtt
from pydantic import BaseModel

from hue2mqtt.config import MQTTBrokerInfo

from .topic import Topic

LOGGER = logging.getLogger(__name__)

Handler = Callable[[Match[str], str], Coroutine[Any, Any, None]]


class MQTTWrapper:
    """
    MQTT wrapper class.

    Wraps the functionality that we are using for MQTT, with extra
    sanity checks and validation to make sure that things are less
    likely to go wrong.
    """

    _client: gmqtt.Client

    def __init__(
        self,
        client_name: str,
        broker_info: MQTTBrokerInfo,
        *,
        last_will: Optional[BaseModel] = None,
    ) -> None:
        self._client_name = client_name
        self._broker_info = broker_info
        self._last_will = last_will
        self._cache = {}

        self._topic_handlers: Dict[Topic, Handler] = {}

        self._client = gmqtt.Client(
            self._client_name,
            will_message=self.last_will_message,
        )

        self._client.reconnect_retries = 0

        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect

    @property
    def is_connected(self) -> bool:
        """Determine if the client connected to the broker."""
        return self._client.is_connected

    @property
    def last_will_message(self) -> Optional[gmqtt.Message]:
        """Last will and testament message for this client."""
        if self._last_will is not None:
            return gmqtt.Message(
                self.mqtt_prefix + "/" + "status",
                self._last_will.json(),
                retain=True,
            )
        else:
            return None

    @property
    def mqtt_prefix(self) -> str:
        """The topic prefix for MQTT."""
        return self._broker_info.topic_prefix

    async def connect(self) -> None:
        """Connect to the broker."""
        if self.is_connected:
            LOGGER.error("Attempting connection, but client is already connected.")
        mqtt_version = gmqtt.constants.MQTTv50
        if self._broker_info.force_protocol_version_3_1:
            mqtt_version = gmqtt.constants.MQTTv311

        if self._broker_info.enable_auth:
            LOGGER.debug("MQTT Auth enabled")
            self._client.set_auth_credentials(
                self._broker_info.username,
                self._broker_info.password,
            )

        await self._client.connect(
            self._broker_info.host,
            port=self._broker_info.port,
            ssl=self._broker_info.enable_tls,
            version=mqtt_version,
        )

    async def disconnect(self) -> None:
        """Disconnect from the broker."""
        if not self.is_connected:
            LOGGER.error(
                "Attempting disconnection, but client is already disconnected.",
            )

        await self._client.disconnect()

        if self.is_connected:
            raise RuntimeError("Disconnection was attempted, but was unsuccessful")

    def on_connect(
        self,
        client: gmqtt.client.Client,
        flags: int,
        rc: int,
        properties: Dict[str, List[int]],
    ) -> None:
        """Callback for mqtt connection."""
        for topic in self._topic_handlers:
            LOGGER.debug(f"Subscribing to {topic}")
            client.subscribe(str(topic))

    async def on_message(
        self,
        client: gmqtt.client.Client,
        topic: str,
        payload: bytes,
        qos: int,
        properties: Dict[str, int],
    ) -> gmqtt.constants.PubRecReasonCode:
        """Callback for mqtt messages."""
        LOGGER.debug(f"Message received on {topic} with payload: {payload!r}")
        for t, handler in self._topic_handlers.items():
            match = t.match(topic)
            if match:
                LOGGER.debug(f"Calling {handler.__name__} to handle {topic}")
                asyncio.ensure_future(handler(match, payload.decode()))

        return gmqtt.constants.PubRecReasonCode.SUCCESS

    def publish(
        self,
        topic: str,
        payload: BaseModel,
        *,
        auto_prefix_topic: bool = True
    ) -> None:
        """Wrapper to publish a payload to the broker."""
        if not self.is_connected:
            LOGGER.error(
                "Attempted to publish message, but client is not connected.",
            )

        prefix = self._broker_info.topic_prefix

        if len(topic) == 0:
            topic_complete = Topic.parse(prefix)
        elif auto_prefix_topic:
            topic_complete = Topic.parse(f"{prefix}/{topic}")
        else:
            topic_complete = Topic.parse(topic)

        if not topic_complete.is_publishable:
            raise ValueError(f"Cannot publish to MQTT topic: {topic_complete}")
 
        if self._broker_info.topic_distinct:
            self._walk_dict(
                str(topic_complete),
                payload.dict(),
            )
        else:
            self._publish(
                str(topic_complete), 
                payload.json(by_alias=True, exclude_none=True)
            )

    def subscribe(
        self,
        topic: str,
        callback: Handler,
    ) -> None:
        """
        Subscribe to an MQTT Topic.

        Callback is called when a message arrives.

        Should be called before the MQTT wrapper is connected.
        """
        if len(topic) == 0:
            topic_complete = Topic.parse(self.mqtt_prefix)
        else:
            topic_complete = Topic.parse(f"{self._broker_info.topic_prefix}/{topic}")

        self._topic_handlers[topic_complete] = callback

    def _publish(
            self,
            topic: str,
            payload: str
        ) -> None:
        """
        Publish a payload to the broker.
        
        Respect message_cache option.
        
        Should only by called by publish and _walk_dict methods.
        """
        publish = True
        if topic in self._cache:
            publish = self._cache[topic] != payload
        
        if publish:
            if self._broker_info.messages_cache:
                self._cache[topic] = payload
                
            self._client.publish(
                topic,
                payload,
                qos=self._broker_info.messages_qos,
                retain=self._broker_info.messages_retain,
            )
        
    def _walk_dict(
            self,
            topic: str,
            payload: dict
        ) -> None:
        """
        Publishes every key-value pair in a dictionary to the broker.
        
        Should only by called by publish and _walk_dict methods.
        """
        for attribute in payload.items():
            topic_complete = "{0}/{1}".format(topic, attribute[0])
            value = attribute[1]
            if isinstance(value, Dict):
                self._walk_dict(
                    topic_complete, 
                    value
                )
            elif value != None:
                self._publish(
                    topic_complete, 
                    dumps(value)
                )
        
            