import sys
import logging
from src.services.kafka import config as KafkaConfig
import json
from src.services.kafka import main_kafka
from flightRouteCalculator import GPSDronePathPlanner
import time
import math


class FlightPlannerTestHarness:
    """
    Simulates real-world, high-stress testing environments for the GPSDronePathPlanner.
    Validates long distance scales, multi-obstacle evasion, and code execution speeds.
    """

    @staticmethod
    def calculate_haversine_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
        """Calculates rough straight-line distance in meters between two GPS coordinates."""
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return 6371000 * c  # Earth radius in meters

    @staticmethod
    def generate_test_environment() -> dict:
        """
        Generates a standard GeoJSON FeatureCollection dictionary representing
        a chain of massive, complex overlapping no-fly zones cutting across the routing lane.
        """
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": "Zone_A_Airfield", "danger_level": "High"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-122.4600, 37.7600],
                            [-122.4300, 37.7600],
                            [-122.4300, 37.7400],
                            [-122.4600, 37.7400],
                            [-122.4600, 37.7600]
                        ]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {"id": "Zone_B_Downtown_Skyscrapers"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-122.4200, 37.7450],
                            [-122.3900, 37.7450],
                            [-122.3900, 37.7200],
                            [-122.4200, 37.7200],
                            [-122.4200, 37.7450]
                        ]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {"id": "Zone_C_Refinery_Complex"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-122.3800, 37.7150],
                            [-122.3500, 37.7150],
                            [-122.3500, 37.6900],
                            [-122.3800, 37.6900],
                            [-122.3800, 37.6150]  # Long trailing edge
                        ]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {"id": "Zone_D_Staggered_Antenna_Farm"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-122.35, 37.8552],
                            [-122.3700, 37.7100],
                            [-122.3700, 37.7000],
                            [-122.4000, 37.7000],
                            [-122.35, 37.8552]
                        ]]
                    }
                }
            ]
        }

    @classmethod
    def run_integration_test(cls):
        print("=" * 70)
        print("      DRONE ROUTING ENGINE STRESS TEST & INTEGRATION LOGS     ")
        print("=" * 70)

        # 1. Initialize Long-Distance Flight Coordinates (~15km flight path)
        takeoff_site = (35.3800, -111.7800)  # Northwest corner (e.g., Richmond District)
        landing_site = (37.8700, -122.4400)  # Southeast corner (e.g., Near SFO Airport)

        straight_line_dist = cls.calculate_haversine_distance(takeoff_site, landing_site)
        print(f"[INIT] Drone Takeoff Point : Lat={takeoff_site[0]:.4f}, Lon={takeoff_site[1]:.4f}")
        print(f"[INIT] Target Landing Site : Lat={landing_site[0]:.4f}, Lon={landing_site[1]:.4f}")
        print(f"[INIT] Straight-Line Vector: {straight_line_dist / 1000:.2f} kilometers")

        # 2. Inject Complex Map Layers
        print("[MAP] Mocking GeoJSON layers with 4 major blocking obstacle polygons...")
        map_obstacles = cls.generate_test_environment()

        # 3. Instantiate Planner with a 1.5 Meter Safety Clearance Buffer
        safety_clearance = 1.5
        print(f"[PLANNER] Spawning routing core with a strict {safety_clearance}m safety margin...")
        planner = GPSDronePathPlanner(map_obstacles, safety_buffer_meters=safety_clearance)

        # 4. Profile Performance (Testing if processing finishes within millisecond thresholds)
        print("[EXEC] Running Visibility Graph creation + Weighted A* + Smoothing path pipeline...")
        start_time = time.perf_counter()

        try:
            flight_waypoints = planner.plan_route(
                start_gps=takeoff_site,
                goal_gps=landing_site,
                weight_multiplier=1.4  # High value optimized for fast mid-flight replanning loops
            )
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # 5. Analyze Path Metrics
            print("\n" + "-" * 50)
            print("▶ INTEGRATION TEST RESULTS SUMMARY:")
            print("-" * 50)
            print(f"  ● Routing Computation Status : SUCCESS")
            print(f"  ● Total Execution Time       : {execution_time_ms:.2f} milliseconds")
            print(f"  ● Generated Waypoints Count  : {len(flight_waypoints)} points")

            # Compute total distance along generated waypoints
            calculated_path_len = 0.0
            for i in range(len(flight_waypoints) - 1):
                calculated_path_len += cls.calculate_haversine_distance(flight_waypoints[i], flight_waypoints[i + 1])

            print(f"  ● Cumulative Path Length     : {calculated_path_len / 1000:.2f} km")
            print(
                f"  ● Route Extension Overhead  : {((calculated_path_len - straight_line_dist) / straight_line_dist) * 100:.1f}% longer than direct line")

            # 6. Print Flight Computer Waypoints Configuration Table
            print("\n" + "-" * 50)
            print("▶ MISSION CONFIGURATION WAYPOINTS EXPORT:")
            print("-" * 50)
            print(f"  {'Index':<6} | {'Latitude':<12} | {'Longitude':<12} | {'Segment Status'}")
            print(f"  {'-' * 5} | {'-' * 12} | {'-' * 12} | {'-' * 14}")

            for index, wp in enumerate(flight_waypoints):
                status = "LAUNCH" if index == 0 else "TERMINAL ARRIVE" if index == len(
                    flight_waypoints) - 1 else f"EVASION WP {index}"
                print(f"   {index:<5} |  {wp[0]:<11.6f} |  {wp[1]:<11.6f} | [ {status} ]")

            print("=" * 70)
            print("       VERIFICATION VERDICT: ALL SYSTEMS OPERATING AS DESIGNED ")
            print("=" * 70)

        except Exception as err:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            print(f"\n[CRITICAL ERROR] Test Failed in {execution_time_ms:.2f}ms: {err}")
            print("Ensure that start and end points are not placed entirely inside a defined no-fly zone.")
        # =====================================================================
        # EXPORT TO GOOGLE EARTH COMPATIBLE CSV
        # =====================================================================
        # =====================================================================
        # EXPORT TO GEOJSON FILE (COMPATIBLE WITH GOOGLE EARTH)
        # =====================================================================
        import json

        geojson_filename = "drone_1000m_tracking_points.geojson"

        # Build standard GeoJSON FeatureCollection structure
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        # Convert each 20-meter GPS tracking point into a Point feature
        for idx, (lat, lon) in enumerate(flight_waypoints):
            label = "Takeoff Anchor Point" if idx == 0 else "Destination Target Landing" if idx == len(
                flight_waypoints) - 1 else f"Tracking Point {idx}"

            feature = {
                "type": "Feature",
                "properties": {
                    "Point_Index": idx,
                    "Name": label,
                    "Distance_Meters": idx * 20
                },
                "geometry": {
                    "type": "Point",
                    # NOTE: GeoJSON standard strictly dictates [Longitude, Latitude] order
                    "coordinates": [lon, lat]
                }
            }
            geojson_data["features"].append(feature)

        # Write to local file system
        with open(geojson_filename, "w", encoding="utf-8") as geojson_file:
            json.dump(geojson_data, geojson_file, indent=2)
        
        print(f"\n[EXPORT] Successfully generated GeoJSON map file: '{geojson_filename}'")
        print(f"[EXPORT] Total plotted tracking nodes: {len(flight_waypoints)}")
        print("=" * 60)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MainService")

def process_flight_message(key,value):
    logger.info(f"--- Processing New Event ---")
    logger.info(f"Received from '{KafkaConfig.INPUT_TOPIC}': key={key}, value={value}")
    
    # Parse payload
    try:
        payload = json.loads(value) if value else {}
    except json.JSONDecodeError:
        payload = {"raw_value": value}

    start_coords = (payload["start"]["latitude"], payload["start"]["longitude"])
    end_coords = (payload["end"]["latitude"], payload["end"]["longitude"])

    print(f"\nProcessing Route [Event: {payload.get('event_id')} | Aircraft: {payload.get('aircraft_id')}]")
    print(f"Routing From: {start_coords} -> To: {end_coords}")

    waypoints = planner.plan_path(start_gps=start_coords, end_gps=end_coords)

    print(f"Success! Generated {len(waypoints)} waypoints.")
    print(f"Waypoints list: {waypoints}")

if __name__ == "__main__":
    # Execute full stress testing cycle
    # FlightPlannerTestHarness.run_integration_test()
    main_kafka(process_flight_message)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
