from confluent_kafka import Producer, Consumer
import json
from flightRouteCalculator import GPSDronePathPlanner


def read_config():
  # reads the client configuration from client.properties
  # and returns it as a key-value map
  config = {}
  with open("client.properties") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

def produce(topic, config):
  # creates a new producer instance
  producer = Producer(config)

  # produces a sample message
  key = "key"
  value = "value"
  producer.produce(topic, key=key, value=value)
  print(f"Produced message to topic {topic}: key = {key:12} value = {value:12}")

  # send any outstanding or buffered messages to the Kafka broker
  producer.flush()

def consume(topic, config):
  # sets the consumer group ID and offset
  config["group.id"] = "python-group-1"
  config["auto.offset.reset"] = "earliest"

  # creates a new consumer instance
  consumer = Consumer(config)

  # subscribes to the specified topic
  consumer.subscribe([topic])
  # TODO Get the Polygons from the DB
  import json
  with open("../polygons.geojson", "r") as f:
    geojson_zones = json.load(f)
  # Instantiate this with your restricted zones GeoJSON data before the loop starts
  planner = GPSDronePathPlanner(geojson_no_fly_zones=geojson_zones, safety_buffer_meters=1.0)

  try:
    while True:
      # consumer polls the topic and prints any incoming messages
      msg = consumer.poll(1.0)
      # --- ADD THIS CODE INSIDE YOUR "while True" KAFKA CONSUMER POOL LOOP ---
      if msg is not None and msg.error() is None:
        try:
          # 1. Parse the incoming JSON message payload
          import json
          payload = json.loads(msg.value().decode("utf-8"))

          # 2. Extract structural telemetry coordinates into tuples (lat, lon)
          start_coords = (payload["start"]["latitude"], payload["start"]["longitude"])
          end_coords = (payload["end"]["latitude"], payload["end"]["longitude"])

          # 3. Print operational tracking logging context
          print(f"\nProcessing Route [Event: {payload.get('event_id')} | Aircraft: {payload.get('aircraft_id')}]")
          print(f"Routing From: {start_coords} -> To: {end_coords}")

          # 4. Invoke your GPS path planner instance
          # (Assumes your planner object is instantiated as 'planner')
          waypoints = planner.plan_path(start_gps=start_coords, end_gps=end_coords)

          # 5. Output calculated flight path telemetry vectors
          print(f"Success! Generated {len(waypoints)} waypoints.")
          print(f"Waypoints list: {waypoints}")

        except KeyError as ke:
          print(f"Payload schema layout error. Missing property field: {ke}")
        except Exception as e:
          print(f"Failed to calculate drone flight path: {e}")

  except KeyboardInterrupt:
    pass
  finally:
    # closes the consumer connection
    consumer.close()

def main():
  config = read_config()
  topic = "event.aircraft.context.ai.reccomendation"

  produce(topic, config)
  consume(topic, config)


main()