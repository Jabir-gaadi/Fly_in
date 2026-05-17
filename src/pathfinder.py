from dataclasses import dataclass
from models import MapData
from graph import Graph


@dataclass
class DroneState:
    """the information that we need to keep track of for each drone
    in simulation
    """
    drone_id: int
    current_zone: str
    path: list[str]
    path_index: int
    in_transit: bool
    arrival_turn: int | None
    delivered: bool


class Pathfinder:
    def __init__(self, graph: Graph, map_data: MapData) -> None:
        self.graph = graph
        self.map_data = map_data
        self.drones: list[DroneState] = []

    def find_n_paths(self, start, end, n=None) -> list[list[str]]:
        if n is None:
            n = self.map_data.nb_drones
        paths: list[list[str]] = []
        found_path: set[tuple[str]] = set()
        penalties: dict[str, float] = {}
        for _ in range(n):
            path = self.just_find_path(start, end, penalties)
            if path is None or tuple(path) in found_path:
                break
            found_path.add(tuple(path))
            paths.append(path)
            for zone in path:
                if zone != start and zone != end:
                    penalties[zone] = penalties.get(zone, 0.0) + 0.5
        return paths

    def just_find_path(
        self, start: str, end: str,
        penalties: dict[str, float] | None = None
    ) -> list[str] | None:
        """
        Find the shortest cost from start to end by implementing Dijkstra
        algo

        Args:
            start: name of starting zone
            end: name of destination zone

        Returns:
            list of zones that show the path, or None if no exesting path
        """
        if penalties is None:
            penalties = {}

        if start != self.map_data.start_hub or end != self.map_data.end_hub:
            return None
        if not self.graph.can_enter(start) or not self.graph.can_enter(end):
            return None

        costs: dict[str, int | float] = {}
        parent: dict[str, str | None] = {}
        for zone in self.map_data.zones.keys():
            costs[zone] = float('inf')
            parent[zone] = None
        costs[start] = 0
        visited: set[str] = set()

        while True:
            lowest_cost = min((zone for zone in costs
                               if zone not in visited and
                               costs[zone] != float('inf')),
                              key=lambda zone: costs[zone])
            if not lowest_cost:
                return None
            if lowest_cost == end:
                break
            visited.add(lowest_cost)
            for neighbor in self.graph.get_neighbors(lowest_cost):
                if neighbor in visited:
                    continue
                if not self.graph.can_enter(neighbor):
                    continue
                neighbor_cost = (self.graph.get_zone_cost(neighbor) +
                                 penalties.get(neighbor, 0.0))
                new_cost = costs[lowest_cost] + neighbor_cost
                if new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = lowest_cost
        my_zone: str = end
        reverse_path: list[str] = [end]
        while my_zone != start:
            parent_zone = parent[my_zone]
            if parent_zone is None:
                break
            my_zone = parent_zone
            reverse_path.append(my_zone)

        if my_zone != start:
            return None
        return reverse_path[::-1]

    def find_all_paths(self) -> bool:
        """
        find multiple paths ans assign each path to a drone

        Args:
            self: Reference to the Pathfinder instance

        Returns:
            True if each drone take a path
            otherwise false
        """
        if self.map_data.nb_drones is None:
            return False

        # find multiple paths
        candidate_paths = self.find_n_paths(
            self.map_data.start_hub,
            self.map_data.end_hub,
            n=2
        )

        if not candidate_paths:
            return False

        # devise the paths to my drnes
        if len(candidate_paths) < self.map_data.nb_drones:
            candidate_paths = [
                candidate_paths[i % len(candidate_paths)]
                for i in range(self.map_data.nb_drones)
            ]

        # Assign kola drone to a path
        for drone_id in range(self.map_data.nb_drones):
            path = candidate_paths[drone_id]
            drone_state = DroneState(
                drone_id=drone_id,
                current_zone=self.map_data.start_hub,
                path=path,
                path_index=1,
                in_transit=False,
                arrival_turn=None,
                delivered=False
            )
            self.drones.append(drone_state)

        return True
