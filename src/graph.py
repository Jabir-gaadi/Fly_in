from models import MapData, Connection


class Graph:
    def __init__(self, map_data: MapData) -> None:
        self.nb_drones = map_data.nb_drones
        self.zones = map_data.zones
        self.connections = map_data.connections
        self.start = map_data.start_hub
        self.end = map_data.end_hub

    def get_neighbors(self, zone_name: str) -> list[str]:
        neighbors: list[str] = []
        for conn in self.connections:
            if conn.zone1 == zone_name:
                neighbors.append(conn.zone2)
            if conn.zone2 == zone_name:
                neighbors.append(conn.zone1)
        return neighbors

    def get_edge(self, zone1: str, zone2: str) -> Connection | None:
        for conn in self.connections:
            if (
                (conn.zone1 == zone1 and conn.zone2 == zone2)
                or
                (conn.zone1 == zone2 and conn.zone2 == zone1)
            ):
                return conn
        return None

    def is_connected(self, zone1: str, zone2: str) -> bool:
        return True if self.get_edge(zone1, zone2) is not None else False

    def get_zone_cost(self, zone_name: str) -> int:
        if zone_name not in self.zones:
            raise ValueError(f"Unknown zone : {zone_name}")
        zone = self.zones[zone_name]
        if zone.zone_type == "restricted":
            return 2
        else:
            return 1

    def can_enter(self, zone_name: str) -> bool:
        if zone_name not in self.zones:
            return False
        zone = self.zones[zone_name]
        return False if zone.zone_type == "blocked" else True

    def find_path(self, start: str, end: str) -> list[str] | None:
        if start not in self.zones or end not in self.zones:
            return None
        if not (self.can_enter(start)) or not (self.can_enter(end)):
            return None
        queue: list[str] = [start]
        visited: set[str] = {start}
        parent: dict[str, str | None] = {start: None}

        while queue:
            current = queue.pop(0)
            if current == end:
                path: list[str] = []
                tmp_node: str | None = end
                while tmp_node is not None:
                    path.insert(0, tmp_node)
                    tmp_node = parent[tmp_node]
                return path
            neighbors: list[str] = self.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited and self.can_enter(neighbor):
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        return None
