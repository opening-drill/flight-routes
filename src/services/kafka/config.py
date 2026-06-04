import os

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "pkc-619z3.us-east1.gcp.confluent.cloud:9092")
SECURITY_PROTOCOL = os.getenv('SECURITY_PROTOCOL', 'SASL_SSL')
SASL_MECHANISMS = os.getenv('SASL_MECHANISMS', 'PLAIN')
SASL_USERNAME = os.getenv('SASL_USERNAME', 'KQ5O3KDKWXHUKE22')
SASL_PASSWORD = os.getenv('SASL_PASSWORD', 'cfltVFvW6XoewHBSrckHgr54ipLlwx7P2tHwVQL3OuVEqI4fWMvrzuJ/CzSxFMoA')
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "flight-routes")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "events")
SESSION_TIMEOUT = os.getenv("SESSION_TIMEOUT", 45000)

kafka_config = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': SECURITY_PROTOCOL,
    'sasl.mechanisms': SASL_MECHANISMS,
    'sasl.username': SASL_USERNAME,
    'sasl.password': SASL_PASSWORD,
    'session.timeout.ms': SESSION_TIMEOUT,
}