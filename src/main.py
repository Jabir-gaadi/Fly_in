import sys
from pathlib import Path

from parser import parse_map_file
from graph import Graph
from pathfinder import Pathfinder
from simulation import Simulation
from visualization import Visualizer


if __name__ == "__main__":
    """Main entry point for the drone routing simulation.

    Parses command-line arguments, runs the simulation, and outputs
    results according to the specification format.
    """
    map_file = sys.argv[1]

    if not Path(map_file).exists():
        print(f"Error: Map file not found: {map_file}", file=sys.stderr)
        sys.exit(1)

    try:
        map_data = parse_map_file(map_file)

        graph = Graph(map_data)

        pathfinder = Pathfinder(graph, map_data)
        if not pathfinder.find_all_paths():
            print("Error: Could not find paths for all drones",
                  file=sys.stderr)
            sys.exit(1)

        simulation = Simulation(pathfinder)
        if not simulation.simulate():
            print("Error: Simulation failed", file=sys.stderr)
            sys.exit(1)

        simulation.output_results()

        # ✅ Fixed: Pass map_data, pathfinder, and movements
        vis = Visualizer(map_data, pathfinder, simulation.movements,
                         interval=2000)
        vis.show()

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
