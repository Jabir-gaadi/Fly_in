import matplotlib.pyplot as plt
from matplotlib.colors import is_color_like
from matplotlib.text import Text

from models import MapData
from pathfinder import Pathfinder


class Visualizer:
    """Draw and animate drone movements on a matplotlib graph."""

    def __init__(
        self,
        map_data: MapData,
        pathfinder: Pathfinder,
        movements: list[list[str]],
        interval: int = 2000,
    ) -> None:
        self.map_data = map_data
        self.movements = movements

        self.fig, self.ax = plt.subplots(figsize=(15, 10))
        self.drone_points: dict[int, Text] = {}

        self._draw_static()
        self._draw_drones()
        self._build_history()

    # ── static map ────────────────────────────────────────────────────────

    def _valid_color(self, color: str | None) -> str:
        if color and is_color_like(color):
            return color
        return "gray"

    def _draw_static(self) -> None:
        self.ax.clear()
        self.ax.axis("off")

        for conn in self.map_data.connections:
            z1 = self.map_data.zones[conn.zone1]
            z2 = self.map_data.zones[conn.zone2]
            self.ax.plot(
                [z1.x, z2.x], [z1.y, z2.y], color="black", linewidth=3
                )

        for zone in self.map_data.zones.values():
            self.ax.scatter(
                zone.x, zone.y, s=2000, zorder=3, linewidth=2,
                edgecolors="black", color=self._valid_color(zone.color),
            )
            self.ax.text(
                zone.x, zone.y - 0.55, zone.name,
                ha="center", va="top", fontsize=7, color="black",
            )

    def _draw_drones(self) -> None:
        nb = self.map_data.nb_drones or 0
        sx = self.map_data.zones[self.map_data.start_hub].x
        sy = self.map_data.zones[self.map_data.start_hub].y
        for i in range(nb):
            point = self.ax.text(
                sx, sy, f"D{i}",
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="white",
                bbox=dict(facecolor="black", edgecolor="white",
                          boxstyle="circle,pad=0.5"),
                zorder=5,
            )
            self.drone_points[i] = point

    # ── history ───────────────────────────────────────────────────────────

    def _build_history(self) -> None:
        """Build per-turn positions from movements list."""
        nb = self.map_data.nb_drones or 0
        pos = {i: self.map_data.start_hub for i in range(nb)}

        # history[turn] = {drone_id: (x, y)}
        self.history: list[dict[int, tuple[float, float]]] = []
        self.history.append(self._positions_to_coords(pos))

        for turn_mvs in self.movements:
            for token in turn_mvs:
                parts = token.split("-")
                if not parts[0].startswith("D"):
                    continue
                try:
                    did = int(parts[0][1:])
                except ValueError:
                    continue

                if len(parts) == 3:
                    # Transit token: D<id>-<to>-<from>  → midpoint
                    to_zone = self.map_data.zones.get(parts[1])
                    from_zone = self.map_data.zones.get(parts[2])
                    if to_zone and from_zone:
                        pos[did] = f"__mid__{parts[2]}__{parts[1]}"
                elif len(parts) == 2:
                    # Normal token: D<id>-<zone>
                    if parts[1] in self.map_data.zones:
                        pos[did] = parts[1]

            self.history.append(self._positions_to_coords(pos))

    def _positions_to_coords(
        self, pos: dict[int, str]
    ) -> dict[int, tuple[float, float]]:
        coords = {}
        for did, p in pos.items():
            if p.startswith("__mid__"):
                _, _, z1, z2 = p.split("__", 3)
                zone1 = self.map_data.zones.get(z1)
                zone2 = self.map_data.zones.get(z2)
                if zone1 and zone2:
                    coords[did] = (
                        (zone1.x + zone2.x) / 2,
                        (zone1.y + zone2.y) / 2,
                    )
            else:
                zone = self.map_data.zones.get(p)
                if zone:
                    coords[did] = (float(zone.x), float(zone.y))
        return coords

    # ── animation ─────────────────────────────────────────────────────────

    def show(self) -> None:
        plt.ion()
        plt.show()

        for turn, frame in enumerate(self.history):
            self.ax.set_title(f"Fly-in Drone Simulation — Turn {turn}")
            for did, (x, y) in frame.items():
                self.drone_points[did].set_position((x, y))
            plt.pause(0.5)

        plt.ioff()
        plt.show()
