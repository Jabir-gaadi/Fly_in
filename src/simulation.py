from pathfinder import Pathfinder


class Simulation:
    """
    Handles turn-by-turn simulation of drone movements
    """
    def __init__(self, pathfinder: Pathfinder) -> None:
        self.pathfinder = pathfinder
        self.movements: list[list[str]] = []

    def simulate(self) -> bool:
        turn: int = 0
        while True:
            self.execute_turn(turn)
            all_delivered = all(drone.delivered
                                for drone in self.pathfinder.drones)
            if all_delivered:
                break
            turn += 1
            if turn == 10000:
                return False
        return True

    def execute_turn(self, turn: int) -> None:
        turn_movements: list[str] = []
        moved_drones: set[int] = set()
        link_usage: dict[tuple[str, str], int] = {}

        # PHASE 1: arrive from restricted zones
        for drone in self.pathfinder.drones:
            if drone.in_transit and drone.arrival_turn is not None:
                if turn >= drone.arrival_turn:
                    next_zone = drone.path[drone.path_index]
                    drone.current_zone = next_zone
                    drone.path_index += 1
                    drone.in_transit = False
                    drone.arrival_turn = None
                    turn_movements.append(f"D{drone.drone_id}-{next_zone}")
                    moved_drones.add(drone.drone_id)

        # PHASE 2: move normal drones
        for drone in self.pathfinder.drones:
            if (
                drone.delivered or
                drone.in_transit or
                drone.drone_id in moved_drones
                    ):
                continue
            if drone.path_index >= len(drone.path):
                continue

            next_zone = drone.path[drone.path_index]
            current_zone = drone.current_zone

        # FIX 1: check link capacity BEFORE anything else (including end_hub)
            connection = self.pathfinder.graph.get_edge(
                current_zone, next_zone)
            if connection is None:
                continue

            sorted_zones = sorted([current_zone, next_zone])
            link_id: tuple[str, str] = (sorted_zones[0], sorted_zones[1])
            if link_usage.get(link_id, 0) >= connection.max_link_capacity:
                continue

            # restricted zone → start 2-turn transit
            zone_type = self.pathfinder.map_data.zones[next_zone].zone_type
            if zone_type == "restricted":
                drone_arriving = 0
                drones_already_there = 0

                for var in self.pathfinder.drones:
                    if (
                        not var.in_transit
                        and
                        var.current_zone == next_zone
                            ):
                        drones_already_there += 1
                    if (
                        var.in_transit
                        and
                        var.path_index < len(var.path)
                        and
                        var.path[var.path_index] == next_zone
                            ):
                        drone_arriving += 1
                zone_capacity = self.pathfinder.map_data.zones[next_zone].\
                    max_drones
                if drone_arriving + drones_already_there >= zone_capacity:
                    continue

                drone.in_transit = True
                drone.arrival_turn = turn + 1
                turn_movements.append(f"D{drone.drone_id}-{next_zone}-\
{current_zone}")
                continue

            # FIX 2: count only drones entering next_zone THIS turn
        # (drones already in next_zone) - (drones leaving next_zone this turn)
            drones_already_there = sum(
                1 for d in self.pathfinder.drones
                if d.current_zone == next_zone and not d.in_transit
                and d.drone_id not in moved_drones
            )

            is_end = next_zone == self.pathfinder.map_data.end_hub
            zone_capacity = self.pathfinder.map_data.zones[next_zone].\
                max_drones

            if not is_end and drones_already_there >= zone_capacity:
                continue

            # perform move
            drone.current_zone = next_zone
            drone.path_index += 1
            link_usage[link_id] = link_usage.get(link_id, 0) + 1
            turn_movements.append(f"D{drone.drone_id}-{next_zone}")
            moved_drones.add(drone.drone_id)

            if is_end:
                drone.delivered = True

        self.movements.append(turn_movements)

    def output_results(self) -> None:
        print("=" * 100)
        print("🚁 SIMULATION EXECUTION")
        print("=" * 100)
        for turn, movements in enumerate(self.movements, 1):
            if movements:
                print(f"  Turn {turn}: {' | '.join(movements)}")
        print("=" * 100)
