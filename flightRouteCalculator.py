import math
from typing import Dict, List, Tuple

import networkx as nx
import pyproj
from shapely.geometry import (
    LineString,
    MultiPolygon,
    Point,
    Polygon,
    shape,
)
from shapely.ops import transform


class GPSDronePathPlanner:
    """
    Visibility-graph drone path planner operating on WGS84 input
    and local metric coordinates internally.
    """

    def __init__(
        self,
        geojson_no_fly_zones: Dict,
        safety_buffer_meters: float = 1.0,
    ):
        self.safety_buffer = safety_buffer_meters
        self.raw_zones_wgs84 = []

        for feature in geojson_no_fly_zones.get("features", []):
            try:
                geom = shape(feature["geometry"])

                if isinstance(geom, Polygon):
                    self.raw_zones_wgs84.append(geom)

                elif isinstance(geom, MultiPolygon):
                    self.raw_zones_wgs84.extend(list(geom.geoms))

            except Exception:
                continue

        if not self.raw_zones_wgs84:
            raise ValueError(
                "No valid polygons found in GeoJSON."
            )

    # ----------------------------------------------------------
    # Coordinate systems
    # ----------------------------------------------------------

    def _init_local_projections(
        self,
        center_lat: float,
        center_lon: float,
    ):
        """
        Creates a local AEQD projection centered on the mission.
        """

        aeqd = (
            f"+proj=aeqd "
            f"+lat_0={center_lat} "
            f"+lon_0={center_lon} "
            f"+x_0=0 +y_0=0 "
            f"+datum=WGS84 "
            f"+units=m "
            f"+no_defs"
        )

        self.wgs84_to_metric = (
            pyproj.Transformer.from_crs(
                "EPSG:4326",
                aeqd,
                always_xy=True,
            ).transform
        )

        self.metric_to_wgs84 = (
            pyproj.Transformer.from_crs(
                aeqd,
                "EPSG:4326",
                always_xy=True,
            ).transform
        )

    def _prepare_buffered_obstacles(self):
        self.buffered_zones_metric = []

        for poly in self.raw_zones_wgs84:
            metric_poly = transform(
                self.wgs84_to_metric,
                poly,
            )

            buffered = metric_poly.buffer(
                self.safety_buffer,
                cap_style=1,
                join_style=1,
            )

            self.buffered_zones_metric.append(buffered)

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    @staticmethod
    def _validate_gps(coord):
        lat, lon = coord

        if not (-90 <= lat <= 90):
            raise ValueError(
                f"Invalid latitude: {lat}"
            )

        if not (-180 <= lon <= 180):
            raise ValueError(
                f"Invalid longitude: {lon}"
            )

    # ----------------------------------------------------------
    # Visibility graph
    # ----------------------------------------------------------

    def _is_line_of_sight_clear(
        self,
        p1: Point,
        p2: Point,
    ) -> bool:

        line = LineString([p1, p2])

        for zone in self.buffered_zones_metric:
            if line.crosses(zone):
                return False

            if line.within(zone):
                return False

            if line.intersects(zone) and not line.touches(zone):
                return False

        return True

    def _build_visibility_graph(
        self,
        start_m: Point,
        goal_m: Point,
    ):
        graph = nx.Graph()

        nodes = [start_m, goal_m]

        for zone in self.buffered_zones_metric:

            simplified = zone.simplify(
                0.25,
                preserve_topology=True,
            )

            for coord in simplified.exterior.coords[:-1]:

                candidate = Point(coord)

                inside_other = any(
                    z.contains(candidate)
                    for z in self.buffered_zones_metric
                )

                if not inside_other:
                    nodes.append(candidate)

        node_map = {
            idx: node
            for idx, node in enumerate(nodes)
        }

        for idx, node in node_map.items():
            graph.add_node(
                idx,
                pos=(node.x, node.y),
            )

        num_nodes = len(nodes)

        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):

                if self._is_line_of_sight_clear(
                    node_map[i],
                    node_map[j],
                ):
                    graph.add_edge(
                        i,
                        j,
                        weight=node_map[i].distance(
                            node_map[j]
                        ),
                    )

        return graph, node_map

    # ----------------------------------------------------------
    # Path smoothing
    # ----------------------------------------------------------

    def _smooth_path(
        self,
        path_nodes: List[Point],
    ) -> List[Point]:

        if len(path_nodes) <= 2:
            return path_nodes

        smoothed = [path_nodes[0]]
        current = 0

        while current < len(path_nodes) - 1:

            next_step = current + 1

            for idx in range(
                len(path_nodes) - 1,
                current,
                -1,
            ):
                if self._is_line_of_sight_clear(
                    path_nodes[current],
                    path_nodes[idx],
                ):
                    next_step = idx
                    break

            if next_step <= current:
                raise RuntimeError(
                    "Path smoothing failed."
                )

            smoothed.append(
                path_nodes[next_step]
            )

            current = next_step

        return smoothed

    # ----------------------------------------------------------
    # Tracking points
    # ----------------------------------------------------------

    def _generate_dense_tracking_points(
        self,
        smoothed_nodes: List[Point],
        interval_meters: float = 20.0,
    ) -> List[Point]:

        if len(smoothed_nodes) < 2:
            return smoothed_nodes

        dense_points = [smoothed_nodes[0]]

        distance_until_next = interval_meters

        for i in range(len(smoothed_nodes) - 1):

            p1 = smoothed_nodes[i]
            p2 = smoothed_nodes[i + 1]

            dx = p2.x - p1.x
            dy = p2.y - p1.y

            seg_len = math.hypot(dx, dy)

            if seg_len == 0:
                continue

            ux = dx / seg_len
            uy = dy / seg_len

            travelled = 0.0

            while (
                travelled + distance_until_next
                <= seg_len
            ):
                travelled += distance_until_next

                dense_points.append(
                    Point(
                        p1.x + ux * travelled,
                        p1.y + uy * travelled,
                    )
                )

                distance_until_next = interval_meters

            leftover = seg_len - travelled
            distance_until_next -= leftover

        if (
            dense_points[-1].distance(
                smoothed_nodes[-1]
            )
            > 0.001
        ):
            dense_points.append(
                smoothed_nodes[-1]
            )

        return dense_points

    # ----------------------------------------------------------
    # Main planner
    # ----------------------------------------------------------

    def plan_route(
        self,
        start_gps: Tuple[float, float],
        goal_gps: Tuple[float, float],
        weight_multiplier: float = 1.3,
        tracking_interval_meters: float = 20.0,
    ):

        self._validate_gps(start_gps)
        self._validate_gps(goal_gps)

        self._init_local_projections(
            center_lat=start_gps[0],
            center_lon=start_gps[1],
        )

        self._prepare_buffered_obstacles()

        start_p = transform(
            self.wgs84_to_metric,
            Point(
                start_gps[1],
                start_gps[0],
            ),
        )

        goal_p = transform(
            self.wgs84_to_metric,
            Point(
                goal_gps[1],
                goal_gps[0],
            ),
        )

        for zone in self.buffered_zones_metric:

            if zone.contains(start_p):
                raise ValueError(
                    "Start position is inside a no-fly zone."
                )

            if zone.contains(goal_p):
                raise ValueError(
                    "Goal position is inside a no-fly zone."
                )

        graph, node_map = (
            self._build_visibility_graph(
                start_p,
                goal_p,
            )
        )

        def heuristic(u, v):
            return (
                node_map[u].distance(node_map[v])
                * weight_multiplier
            )

        try:
            path_ids = nx.astar_path(
                graph,
                source=0,
                target=1,
                heuristic=heuristic,
                weight="weight",
            )

        except nx.NetworkXNoPath:
            raise RuntimeError(
                "No valid route exists."
            )

        raw_nodes = [
            node_map[idx]
            for idx in path_ids
        ]

        smoothed_nodes = self._smooth_path(
            raw_nodes
        )

        dense_nodes = (
            self._generate_dense_tracking_points(
                smoothed_nodes,
                tracking_interval_meters,
            )
        )

        def metric_to_gps(points):

            output = []

            for p in points:

                gps = transform(
                    self.metric_to_wgs84,
                    p,
                )

                output.append(
                    (
                        gps.y,
                        gps.x,
                    )
                )

            return output

        return  metric_to_gps(dense_nodes)
           # metric_to_gps(smoothed_nodes),

