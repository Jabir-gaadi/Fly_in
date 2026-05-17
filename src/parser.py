import sys
from models import MapData, Zone, Connection


def rm_hashtag_line(line: str) -> str:
    index = line.index('#')
    line = line[:index]
    return line


def read_line(path: str) -> list[str]:
    lines = []
    try:
        with open(path, 'r') as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        print(f"File {path} not found.")
        sys.exit(1)
    if len(lines) == 0:
        print("No data read from file.")
        sys.exit(1)
    return lines


def parse_metadata(metadata_str: str) -> dict[str, str]:
    """Parse metadata from string format [key=value key=value ...].

    Args:
        metadata_str: Metadata string with brackets.

    Returns:
        Dictionary of key-value pairs.

    Raises:
        ValueError: If metadata format is invalid.
    """
    metadata_dict: dict[str, str] = {}
    if metadata_str.startswith('[') and metadata_str.endswith(']'):
        metadata_str = metadata_str[1:-1]
        if not metadata_str:
            return metadata_dict
        metadata_items = metadata_str.split()
        for item in metadata_items:
            if '=' not in item:
                raise ValueError(f"Invalid metadata format: {item}")
            parts = item.split('=', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid metadata format: {item}")
            key, value = parts
            if key == "color":
                metadata_dict[key] = value
            elif key == "zone":
                metadata_dict[key] = value
            elif key == "max_drones":
                metadata_dict[key] = value
            elif key == "max_link_capacity":
                metadata_dict[key] = value
            else:
                raise ValueError(f"Unknown key in metadata: {key}")
    return metadata_dict


def final_parse(lines: list[str]) -> MapData:
    map = MapData(
        nb_drones=None,
        zones={},
        connections=[],
        start_hub="",
        end_hub=""
    )
    line_num = 0
    first_line = True

    for line in lines:
        if line.strip().startswith('#'):
            line_num += 1
            continue
        if line.strip() == '':
            line_num += 1
            continue
        if line.strip() == '\n':
            line_num += 1
            continue
        if '#' in line:
            line = rm_hashtag_line(line)
        # print(f"num = {line_num}, line = {line}")
        try:
            if line.startswith("nb_drones") and first_line:
                line_num += 1
                tmp = line.split(':')
                if len(tmp) != 2:
                    raise ValueError("Invalid line of nb_drones")
                try:
                    nb_drones = int(tmp[1])
                    if nb_drones < 1:
                        raise ValueError("nb_drones must be \
a positive integer")
                except ValueError:
                    raise ValueError("Data of nb_drones should be a valid \
number > 0")
                map.nb_drones = nb_drones

            elif line.startswith("nb_drones") and (map.nb_drones or
                                                   not first_line):
                raise ValueError("nb_drones should be defined only once \
and at the beginning of the file")

            elif (
                line.startswith("start_hub")
                or line.startswith("end_hub")
                or line.startswith("hub")
            ):
                line_num += 1
                tmp_zone = Zone(
                    name="",
                    x=0,
                    y=0,
                    zone_type="",
                    color=None,
                    max_drones=1
                )
                all_lines = line.split(':')
                if len(all_lines) != 2:
                    raise ValueError(
                        "line should be like (zone_type: name x y [metadata])"
                    )
                zone_type = all_lines[0]
                if zone_type == "start_hub":
                    tmp_zone.zone_type = "start_hub"
                elif zone_type == "end_hub":
                    tmp_zone.zone_type = "end_hub"
                elif zone_type == "hub":
                    tmp_zone.zone_type = "hub"

                if (
                    all_lines[1].count('[') > 1 or
                    all_lines[1].count(']') > 1
                ):
                    raise ValueError(f"invalid line of {zone_type}")
                parts = all_lines[1].split('[')
                result = parts[0].split()
                if len(parts) > 1:
                    data = "[" + parts[1].split(']')[0] + ']'
                    line_to_check = '[' + all_lines[1].split('[')[1]
                    if data.strip() != line_to_check.strip():
                        raise ValueError(f"Invalid line of this zone: \
{tmp_zone.zone_type}\nshould be like: (zone_type: name x y [metadata])")
                    if ']' not in parts[1]:
                        raise ValueError("Invalid string in Metadata Part")
                    result.append(data.strip())

                rest_of_line = result
                if len(rest_of_line) < 3 or len(rest_of_line) > 4:
                    raise ValueError(
                        "line should be like (zone_type: name x y [metadata])"
                    )
                try:
                    tmp_zone.name = rest_of_line[0]
                    if '-' in tmp_zone.name or ' ' in tmp_zone.name:
                        raise ValueError(
                            f"Zone name cannot contain dashes or spaces: "
                            f"{tmp_zone.name}"
                        )
                    tmp_zone.x = int(rest_of_line[1])
                    tmp_zone.y = int(rest_of_line[2])

                    for zone in map.zones.values():
                        if tmp_zone.x == zone.x and tmp_zone.y == zone.y:
                            raise ValueError(f"{tmp_zone.name} and {zone.name}\
 has the same coordinates")
                    metadata_str = None
                    if len(rest_of_line) == 4:
                        metadata_str = rest_of_line[3]
                except ValueError as e:
                    raise ValueError(
                        f"Invalid zone definition: {str(e)}"
                    )
                valid_metadata: dict[str, str] = {}
                if metadata_str is not None:
                    valid_metadata = parse_metadata(metadata_str)
                if tmp_zone.name in map.zones:
                    raise ValueError(f"Duplicate zone name: {tmp_zone.name}")
                map.zones[tmp_zone.name] = tmp_zone
                if zone_type == "start_hub":
                    if map.start_hub != "":
                        raise ValueError("Multiple start_hub found!")
                    map.start_hub = tmp_zone.name
                elif zone_type == "end_hub":
                    if map.end_hub != "":
                        raise ValueError("Multiple end_hub found!")
                    map.end_hub = tmp_zone.name
                if valid_metadata:
                    if 'color' in valid_metadata:
                        tmp_zone.color = valid_metadata["color"]
                    if 'zone' in valid_metadata:
                        zone_type_value = valid_metadata["zone"]
                        valid_types = {"normal", "blocked", "restricted",
                                       "priority"}
                        if zone_type_value not in valid_types:
                            raise ValueError(
                                f"Invalid zone type: {zone_type_value}. "
                                f"Must be one of {valid_types}"
                            )
                        if (
                            zone_type_value == 'blocked' and
                            tmp_zone.zone_type == 'end_hub'
                        ):
                            raise ValueError('Can\'t set blocked zone to \
the end type')
                        tmp_zone.zone_type = zone_type_value
                    if 'max_drones' in valid_metadata:
                        try:
                            tmp_zone.max_drones = int(
                                valid_metadata["max_drones"]
                            )
                            if tmp_zone.max_drones < 1:
                                raise ValueError(
                                    "max_drones must be a positive integer"
                                )
                        except ValueError:
                            raise ValueError(
                                "max_drones must be a positive integer"
                            )

            elif (
                not line.startswith("start_hub")
                and not line.startswith("end_hub")
                and not line.startswith("hub")
                and not line.startswith("connection")
            ):
                line_num += 1
                raise ValueError("this line start with an unknown word")

            elif line.startswith("connection:"):
                line_num += 1
                tmp = line.split(':')
                if len(tmp) != 2:
                    raise ValueError("Invalid connection line format")

                connection_part = tmp[1].strip()
                connection_items = connection_part.split()
                if len(connection_items) < 1:
                    raise ValueError("Connection must specify zones")

                zones_part = connection_items[0]
                metadata_start = connection_part.find('[')
                if metadata_start != -1:
                    metadata_part = connection_part[metadata_start:].strip()
                else:
                    metadata_part = None

                zone_names = zones_part.split('-')
                if len(zone_names) != 2:
                    raise ValueError(
                        "Connection must have exactly 2 zones "
                        "separated by dash"
                    )

                zone1, zone2 = zone_names[0], zone_names[1]
                rest = line.split(zone2)[1].strip()
                if rest and ('[' not in rest) and (']' not in rest):
                    raise ValueError("Invalid line of this Connection \
should be exact like this : (connection: <name1>-<name2> [metadata])")

                if zone1 not in map.zones:
                    msg = f"Connection references unknown zone: {zone1}"
                    raise ValueError(msg)
                if zone2 not in map.zones:
                    msg = f"Connection references unknown zone: {zone2}"
                    raise ValueError(msg)

                max_link_capacity = 1
                if metadata_part:
                    conn_metadata = parse_metadata(metadata_part)

                    for each_key in conn_metadata.keys():
                        if each_key != 'max_link_capacity':
                            raise ValueError(f"invalid metadata key for \
connection: {each_key}")
                    if 'max_link_capacity' in conn_metadata:
                        try:
                            capacity = int(
                                conn_metadata["max_link_capacity"]
                            )
                            if capacity < 1:
                                raise ValueError(
                                    "max_link_capacity must be a "
                                    "positive integer"
                                )
                            max_link_capacity = capacity
                        except ValueError:
                            raise ValueError(
                                "max_link_capacity must be a "
                                "positive integer"
                            )

                for existing_conn in map.connections:
                    if ((existing_conn.zone1 == zone1 and
                            existing_conn.zone2 == zone2) or (
                        existing_conn.zone1 == zone2 and
                            existing_conn.zone2 == zone1)):
                        raise ValueError(
                            f"Duplicate connection: {zone1}-{zone2}"
                        )

                connection = Connection(
                    zone1=zone1,
                    zone2=zone2,
                    max_link_capacity=max_link_capacity
                )
                map.connections.append(connection)

        except ValueError as e:
            raise ValueError(f"Line {line_num}: {str(e)}")
        first_line = False

    if not map.nb_drones or map.nb_drones == 0:
        raise ValueError("no nb_drones found")

    if map.start_hub == "":
        raise ValueError("No start_hub found in map file")

    if map.end_hub == "":
        raise ValueError("No end_hub found in map file")

    if map.start_hub == map.end_hub:
        raise ValueError("start_hub and end_hub cannot be the same zone")

    return map


def parse_map_file(path: str) -> MapData:
    """Parse a map file and return structured MapData object.

    Args:
        path: Path to the map file.

    Returns:
        MapData object containing all parsed information.

    Raises:
        ValueError: If the file format is invalid.
        FileNotFoundError: If the file does not exist.
    """
    lines = read_line(path)
    return final_parse(lines)
