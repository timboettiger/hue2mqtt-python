"""
Configuration schema for Astoria.

Common to all components.
"""
from pathlib import Path
from typing import IO, Optional

from pydantic import BaseModel, parse_obj_as, ValidationError, validator

# Backwards compatibility for TOML in stdlib from Python 3.11
try:
    import tomllib  # type: ignore[import,unused-ignore]
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import,no-redef,unused-ignore]


class HueBridgeInfo(BaseModel):
    """MQTT Broker Information."""

    ip: str
    username: str

    class Config:
        """Pydantic config."""

        extra = "forbid"


class MQTTBrokerInfo(BaseModel):
    """MQTT Broker Information."""

    host: str
    port: int
    enable_auth: bool = False
    username: str = ""
    password: str = ""
    enable_tls: bool = False
    messages_retain: bool = True    # Sets Retain-flag when messages getting sent
    messages_qos: int = 1           # Sets QoS used when messages getting sent
    messages_cache: bool = True     # Caches topic/value-pairs to only send changes ones
    topic_prefix: str = "hue2mqtt"
    topic_distinct: bool = False    # Publishes all attributes as individual topics
    topic_scheme: str = "id"        # "id": unique identifier id of hue device, "name": name of hue device
    force_protocol_version_3_1: bool = False

    @validator('topic_scheme')
    def valid_topic_scheme(cls, v):
        v = v.lower()
        if v not in ["id", "name"]:
            raise ValueError('must be either "id" or "name"')
        return v

    class Config:
        """Pydantic config."""

        extra = "forbid"


class Hue2MQTTConfig(BaseModel):
    """Config schema for Hue2MQTT."""

    mqtt: MQTTBrokerInfo
    hue: HueBridgeInfo

    class Config:
        """Pydantic config."""

        extra = "forbid"

    @classmethod
    def _get_config_path(cls, config_str: Optional[str] = None) -> Path:
        """Check for a config file or search the filesystem for one."""
        config_search_paths = [
            Path("hue2mqtt.toml"),
            Path("/etc/hue2mqtt.toml"),
        ]
        if config_str is None:
            for path in config_search_paths:
                if path.exists() and path.is_file():
                    return path
        else:
            path = Path(config_str)
            if path.exists() and path.is_file():
                return path
        raise FileNotFoundError("Unable to find config file.")

    @classmethod
    def load(cls, config_str: Optional[str] = None) -> "Hue2MQTTConfig":
        """Load the config."""
        config_path = cls._get_config_path(config_str)
        with config_path.open("rb") as fh:
            return cls.load_from_file(fh)

    @classmethod
    def load_from_file(cls, fh: IO[bytes]) -> "Hue2MQTTConfig":
        """Load the config from a file."""
        return parse_obj_as(cls, tomllib.load(fh))
