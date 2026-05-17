from dataclasses import dataclass
from typing import Optional


@dataclass
class Zone:
    """Representation of a zone in the map"""
    name: str
    x: int
    y: int
    zone_type: str
    color: Optional[str]
    max_drones: int = 1


@dataclass
class Connection:
    """Representation of a connection of two zones"""
    zone1: str
    zone2: str
    max_link_capacity: int = 1


@dataclass
class MapData:
    """The complete map data that parsed from the file"""
    nb_drones: int | None
    zones: dict[str, Zone]
    connections: list[Connection]
    start_hub: str
    end_hub: str
