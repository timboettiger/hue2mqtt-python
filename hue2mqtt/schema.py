"""Schemas for data about lights."""
from enum import Enum
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, Field, create_model


class BatteryState(str, Enum):
    normal = 'normal'
    low = 'low'
    critical = 'critical'


class PowerState(BaseModel):
    """The state of power."""

    battery_level: Optional[int] = None
    battery_state: Optional[BatteryState] = None


class UpdateState(str, Enum):
    not_updatable = 'notupdatable'
    no_updates = 'noupdates'
    

class SoftwareUpdate(BaseModel):
    """The state of software update."""

    lastinstall: Optional[str] = None
    state: Optional[UpdateState] = None


class ColorMode(str, Enum):
    hs = 'hs'
    ct = 'ct'
    xy = 'xy'


class LightBaseState(BaseModel):
    """The base attributes of a light state."""

    on: Optional[bool]

    alert: Optional[str]
    bri: Optional[int]
    ct: Optional[int]
    effect: Optional[str]
    hue: Optional[int]
    sat: Optional[int]
    xy: Optional[Tuple[float, float]] = None


class LightSetState(LightBaseState):
    """The settable states of a light."""

    bri_inc: Optional[int]
    sat_inc: Optional[int]
    hue_inc: Optional[int]
    ct_inc: Optional[int]
    xy_inc: Optional[int]


class LightState(LightBaseState):
    """The State of a light that we can read."""

    reachable: Optional[bool]
    colormode: Optional[ColorMode]
    mode: Optional[str]


class LightInfo(BaseModel):
    """Information about a light."""

    id: int  # noqa: A003
    name: str
    uniqueid: str
    state: Optional[LightState]

    manufacturername: str
    modelid: str
    productname: str
    type: str  # noqa: A003

    swversion: str
    swupdate: Optional[SoftwareUpdate]


class GroupType(str, Enum):
    Luminaire = 'Luminaire'
    Lightsource = 'Lightsource'
    LightGroup = 'LightGroup'
    Room = 'Room'
    Entertainment = 'Entertainment'
    Zone = 'Zone'


class GroupClass(str, Enum):
    living_room = 'Living room'
    recreation = 'Recreation'
    terrace = 'Terrace'
    kitchen = 'Kitchen'
    office = 'Office'
    garden = 'Garden'
    dining = 'Dining'
    gym = 'Gym'
    driveway = 'Driveway'
    bedroom = 'Bedroom'
    hallway = 'Hallway'
    carport = 'Carport'
    kids_bedroom = 'Kids bedroom'
    toilet = 'Toilet'
    other = 'Other'
    bathroom = 'Bathroom'
    front_door = 'Front door'
    nursery = 'Nursery'
    garage = 'Garage'
    home = 'Home'
    lounge = 'Lounge'
    closet = 'Closet'
    downstairs = 'Downstairs'
    man_cave = 'Man cave'
    storage = 'Storage'
    upstairs = 'Upstairs'
    computer = 'Computer'
    laundry_room = 'Laundry room'
    top_floor = 'Top floor'
    studio = 'Studio'
    balcony = 'Balcony'
    attic = 'Attic'
    music = 'Music'
    porch = 'Porch'
    guest_room = 'Guest room'
    television = 'TV'
    barbecue = 'Barbecue'
    staircase = 'Staircase'
    reading = 'Reading'
    pool = 'Pool'


class GroupSetState(LightSetState):
    """The settable states of a group."""

    scene: Optional[str]


class GroupState(BaseModel):
    """The state of lights in a group."""

    all_on: bool
    any_on: bool


class GroupInfo(BaseModel):
    """Information about a light group."""

    id: int  # noqa: A003
    name: str
    lights: List[int]
    sensors: List[int]
    type: GroupType  # noqa: A003
    state: GroupState

    group_class: Optional[GroupClass] = Field(default=None, alias="class")

    action: LightState


class GenericSensorState(BaseModel):
    """Information about the state of a sensor."""

    lastupdated: Optional[str] = None
    power_state: Optional[PowerState] = None


class PresenceSensorState(GenericSensorState):
    """Information about the state of a sensor."""

    presence: Optional[bool] = None


class RotarySensorState(GenericSensorState):
    """Information about the state of a sensor."""

    rotaryevent: Optional[str] = None
    expectedrotation: Optional[str] = None
    expectedeventduration: Optional[str] = None


class SwitchSensorState(GenericSensorState):
    """Information about the state of a sensor."""

    buttonevent: Optional[int] = None


class LightLevelSensorState(GenericSensorState):
    """Information about the state of a sensor."""

    dark: Optional[bool] = None
    daylight: Optional[bool] = None
    lightlevel: Optional[float] = None


class TemperatureSensorState(GenericSensorState):
    """Information about the state of a sensor."""

    temperature: Optional[float] = None


class HumiditySensorState(GenericSensorState):
    """Information about the state of a sensor."""

    humidity: Optional[float] = None


class OpenCloseSensorState(GenericSensorState):
    """Information about the state of a sensor."""

    open: Optional[str] = None  # noqa: A003


SensorState = create_model(
    "SensorState",
    __base__=(
        LightLevelSensorState,
        PresenceSensorState,
        RotarySensorState,
        SwitchSensorState,
        TemperatureSensorState,
        HumiditySensorState,
        OpenCloseSensorState,
    ),
)


class SensorInfo(BaseModel):
    """Information about a sensor."""

    id: int  # noqa: A003
    name: str
    type: str  # noqa: A003
    modelid: str
    manufacturername: str

    productname: str
    uniqueid: str
    swversion: Optional[str]
    swupdate: Optional[SoftwareUpdate]

    power_state: Optional[PowerState] = None
    state: SensorState  # type: ignore[valid-type]
    capabilities: Any
