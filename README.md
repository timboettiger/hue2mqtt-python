# Hue2MQTT

Python Hue to MQTT Bridge

## What and Why?

Hue2MQTT lets you control your Hue setup using MQTT and publishes the current state in real-time.

- Python 3.8+ with type hints and asyncio
- Uses the excellent [aiohue](https://github.com/home-assistant-libs/aiohue) library to communicate with Hue.
- Control your lights using MQTT
- Receive live events (i.e button pushes, motion sensors) in real-time.
- No polling your Hue Bridge for changes
- IPv6 Support

## Configuration

Hue2MQTT is configured using `hue2mqtt.toml`. A default configuration is provided with hue2mqtt.example.toml

### Config Options

`messages_retain`

Set the retain flag for mqtt messages. Possible values are true (enabled) and false (disabled)

`messages_qos`

Define the quality of service respective delivery guarantee for mqtt messages. Can be 0 (at most once), 1 (at least once) or 2 (exactly one).

`messages_cache`

Enables the caching value per topic sent by mqtt to ensure that only modified values are sent. Possible values are true (cache) and false (do not cache).

`topic_prefix`

Set the prefix of the topic for mqtt messages. Can contain any ASCII character, keep in mind that a slash ("/") splits the topic into two or more segments. This is why there must not be a slash at the end of the prefix.

`topic_distinct`
Splits the JSON value of topics into seperate topics by adding segments each for an JSON attribute. Takes into account the nesting of JSON values.

`topic_scheme`

Defines the style of topic structure: Segments of devices are named either by their unique id (00:00:00:00:00:00:00:00-00) or by the speaking name in lowercase assigned in the hue app.

Examples for topics with `topic_distinct` disabled: `/hue2mqtt/light/00:17:88:01:ab:cd:ef:01-02` or `/hue2mqtt/light/lounge lamp`

Examples for topics with `topic_distinct` enabled: `/hue2mqtt/light/00:17:88:01:ab:cd:ef:01-02/state/on` or `/hue2mqtt/light/lounge lamp/state/on`

### Hue2MQTT Default Config File

```toml

[mqtt]
host = "::1"
port = 1883
enable_tls = false
force_protocol_version_3_1 = true

enable_auth = false
clientid = "hue2mqtt"
username = ""
password = ""

messages_retain = true
messages_qos = 1
messages_cache = true

topic_prefix = "hue2mqtt"
topic_distinct = false
topic_scheme = "id"

[hue]
ip = "192.168.0.1"  # or IPv6: "[::ffff:c0a8:1]"
username = "aB1cDEf2Gh3IjklLMNoPqrstuVWxYZAbCdEFg4hi"
```

If you do not know the username for your bridge, find it using `hue2mqtt --discover`.

## Running Hue2MQTT

Usually, it is as simple as running `hue2mqtt`.

```
Usage: hue2mqtt [OPTIONS]

  Main function for Hue2MQTT.

Options:
  -v, --verbose
  -c, --config-file PATH
  --discover
  --help                  Show this message and exit.
```

## Bridge Status

The status of Hue2MQTT is published to `hue2mqtt/status` as a JSON object:

```json
{"online": true, "bridge": {"name": "Philips Hue", "mac_address": "ec:b5:fa:ab:cd:ef", "api_version": "1.45.0"}}
```

If `online` is `false`, then all other information published by the bridge should be assumed to be inaccurate.

The `bridge` object contains information about the Hue Bridge, if available.

## Getting information about Hue

Information about the state of Hue is published to MQTT as retained messages. Messages are re-published when the state changes.

### Lights

Information about lights is published by default to `hue2mqtt/light/{{UNIQUEID}}` where `UNIQUEID` is the Zigbee MAC of the light.

e.g `hue2mqtt/light/00:17:88:01:ab:cd:ef:01-02`

When `topic_scheme` is set to `name`, it will be published to `hue2mqtt/light/{{NAME}}` where `NAME` is the speaking name in lowercase assigned in the hue app to the device.

e.g `hue2mqtt/group/lounge`

```json
{"id": 1, "name": "Lounge Lamp", "uniqueid": "00:17:88:01:ab:cd:ef:01-02", "state": {"on": false, "alert": "none", "bri": 153, "ct": 497, "effect": "none", "hue": 7170, "sat": 225, "xy": [0, 0], "transitiontime": null, "reachable": true, "color_mode": null, "mode": "homeautomation"}, "manufacturername": "Signify Netherlands B.V.", "modelid": "LCT012", "productname": "Hue color candle", "type": "Extended color light", "swversion": "1.50.2_r30933"}

```

### Groups

A group represents a group of lights, referred to as Rooms and Zones in the Hue app.

Information about lights is published by default to `hue2mqtt/group/{{GROUPID}}` where `GROUPID` is an integer.

When `topic_scheme` is set to `name`, it will be published to `hue2mqtt/group/{{NAME}}` where `NAME` is the speaking name in lowercase assigned in the hue app to the device.

e.g `hue2mqtt/group/lounge`

```
hue2mqtt/group/3 {"id": 3, "name": "Lounge", "lights": [24, 21, 20, 3, 5], "sensors": [], "type": "Room", "state": {"all_on": false, "any_on": false}, "group_class": "Living room", "action": {"on": false, "alert": "none", "bri": 153, "ct": 497, "effect": "none", "hue": 7170, "sat": 225, "xy": [0, 0], "transitiontime": null, "reachable": null, "color_mode": null, "mode": null}}
```

### Sensors

Sensors represent other objects in the Hue ecosystem, such as switches and motion sensors. There are also a number of "virtual" sensors that the Hue Hub uses to represent calculated values (e.g `daylight`), but these are ignored by Hue2MQTT.

Information about sensors is published by default to `hue2mqtt/sensor/{{UNIQUEID}}` where `UNIQUEID` is the Zigbee MAC of the device.

e.g `hue2mqtt/sensor/00:17:88:01:ab:cd:ef:01-02`

When `topic_scheme` is set to `name`, it will be published to `hue2mqtt/sensor/{{NAME}}` where `NAME` is the speaking name in lowercase assigned in the hue app to the device.

e.g `hue2mqtt/sensor/lounge switch`

**Switch**

```json
{"id": 10, "name": "Lounge switch", "type": "ZLLSwitch", "modelid": "RWL021", "manufacturername": "Signify Netherlands B.V.", "productname": "Hue dimmer switch", "uniqueid": "00:17:88:01:ab:cd:ef:01-02", "swversion": "6.1.1.28573", "state": {"lastupdated": "2021-07-10T11:37:58", "buttonevent": 4002}, "capabilities": {"certified": true, "primary": true, "inputs": [{"repeatintervals": [800], "events": [{"buttonevent": 1000, "eventtype": "initial_press"}, {"buttonevent": 1001, "eventtype": "repeat"}, {"buttonevent": 1002, "eventtype": "short_release"}, {"buttonevent": 1003, "eventtype": "long_release"}]}, {"repeatintervals": [800], "events": [{"buttonevent": 2000, "eventtype": "initial_press"}, {"buttonevent": 2001, "eventtype": "repeat"}, {"buttonevent": 2002, "eventtype": "short_release"}, {"buttonevent": 2003, "eventtype": "long_release"}]}, {"repeatintervals": [800], "events": [{"buttonevent": 3000, "eventtype": "initial_press"}, {"buttonevent": 3001, "eventtype": "repeat"}, {"buttonevent": 3002, "eventtype": "short_release"}, {"buttonevent": 3003, "eventtype": "long_release"}]}, {"repeatintervals": [800], "events": [{"buttonevent": 4000, "eventtype": "initial_press"}, {"buttonevent": 4001, "eventtype": "repeat"}, {"buttonevent": 4002, "eventtype": "short_release"}, {"buttonevent": 4003, "eventtype": "long_release"}]}]}}
```

**Light Sensor**

```json
{"id": 5, "name": "Hue ambient light sensor 1", "type": "ZLLLightLevel", "modelid": "SML001", "manufacturername": "Signify Netherlands B.V.", "productname": "Hue ambient light sensor", "uniqueid": "00:17:88:01:04:b7:b5:20-02-0400", "swversion": "6.1.1.27575", "state": {"lastupdated": "2021-07-10T12:28:17", "dark": true, "daylight": false, "lightlevel": 14606}, "capabilities": {"certified": true, "primary": false}}
```

**Temperature Sensor**



## Controlling Hue

Lights and Groups can be controlled by publishing objects to the `hue2mqtt/light/{{UNIQUEID}}/set` or `hue2mqtt/group/{{GROUPID}}/set` topics.

The object should be a JSON object containing the state values that you wish to change.

```json
{"on": "true"}
```

## Docker

Included is a basic Dockerfile and docker-compose example. 

### MQTT Connections to the Docker Host

To establish a MQTT-Connection to the Docker Host (localhost is in fact the docker instance itself) use `host.docker.internal` to describe the host within hue2mqtt.toml

```toml
host = "host.docker.internal"
```
