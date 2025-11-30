import requests
import datetime
import json
import os
import logging
from influxdb import InfluxDBClient

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
SCHEMA_CONFIG_FILE = "data/ebusd_data.json"
APP_CONFIG_FILE = "data/config.json"

def load_app_config():
    if not os.path.exists(APP_CONFIG_FILE):
        logging.error(f"Config file '{APP_CONFIG_FILE}' not found.")
        return None
    with open(APP_CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_schema_config():
    if not os.path.exists(SCHEMA_CONFIG_FILE):
        logging.error(f"Schema file '{SCHEMA_CONFIG_FILE}' not found. Run the generator script first.")
        return None
    with open(SCHEMA_CONFIG_FILE, 'r') as f:
        return json.load(f)

def fetch_and_write():
    # 1. Load App Config
    app_config = load_app_config()
    if not app_config or "ebusd" not in app_config or "influxdb" not in app_config:
        logging.error("Failed to load app configuration or 'ebusd' or 'influxdb' settings are missing.")
        return

    ebus_config = app_config.get("ebusd", {})
    INFLUX_SETTINGS = app_config["influxdb"]
    ebusd_http_timeout = ebus_config.get("ebusd_http_timeout", 60)
    
    # 2. Load Schema
    schema = load_schema_config()
    if not schema:
        return

    # 3. Setup InfluxDB
    try:
        client = InfluxDBClient(host=INFLUX_SETTINGS['host'], port=INFLUX_SETTINGS['port'], 
                                username=INFLUX_SETTINGS['user'], password=INFLUX_SETTINGS['pass'], 
                                database=INFLUX_SETTINGS['db'])
        logging.info(f"Connected to InfluxDB at {INFLUX_SETTINGS['host']}:{INFLUX_SETTINGS['port']}, database '{INFLUX_SETTINGS['db']}'")
    except Exception as e:
        logging.error(f"Failed to connect to InfluxDB: {e}")
        return

    urls_processed = 0
    for i in range(1, 5):
        data_url = ebus_config.get(f"ebusd_url_{i}")
        if not data_url:
            continue
        
        urls_processed += 1
        logging.info(f"--- STARTING FETCH FOR {data_url} ---")

        # 4. Fetch Live Data
        try:
            logging.debug(f"Fetching data from {data_url}")
            response = requests.get(data_url, timeout=ebusd_http_timeout)
            response.raise_for_status()
            data = response.json()
            logging.debug(f"Successfully fetched data: {json.dumps(data, indent=2)}")
        except Exception as e:
            logging.error(f"Data fetch for {data_url} failed: {e}")
            continue # Continue to next URL

        points_batch = []

        # 5. Iterate based on keys in the fetched data
        logging.info("Processing data...")
        for measure_name, live_root in data.items():

            if measure_name not in schema:
                continue

            sensors_config = schema[measure_name]

            if not isinstance(live_root, dict) or "messages" not in live_root:
                logging.warning(f"Skipping '{measure_name}' in {data_url}: 'messages' key is missing or data is not a dictionary.")
                continue
            
            live_messages = live_root["messages"]
            collected_fields = {}
            timestamp_to_use = None

            for sensor_name, field_configs in sensors_config.items():
                
                if sensor_name not in live_messages:
                    logging.debug(f"Sensor '{sensor_name}' not in live data for measurement '{measure_name}' from {data_url}.")
                    continue

                sensor_data = live_messages[sensor_name]
                logging.debug(f"Processing sensor: {sensor_name}")
                
                if timestamp_to_use is None and "lastup" in sensor_data:
                    try:
                        ts_epoch = sensor_data["lastup"]
                        ts = datetime.datetime.fromtimestamp(ts_epoch, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        timestamp_to_use = ts
                        logging.debug(f"Using timestamp {ts} from sensor '{sensor_name}'.")
                    except Exception as e:
                        logging.warning(f"Could not parse timestamp from {sensor_data['lastup']}: {e}")

                inner_fields_data = sensor_data.get("fields", {})
                
                for specific_field_key, rules in field_configs.items():
                    
                    if not rules.get("enabled", True):
                        logging.debug(f"Skipping disabled field '{specific_field_key}' in sensor '{sensor_name}'.")
                        continue
                    
                    if specific_field_key in inner_fields_data:
                        
                        data_obj = inner_fields_data[specific_field_key]
                        raw_val = data_obj.get("value")

                        if raw_val is None:
                            logging.debug(f"Skipping field with null value: {specific_field_key}")
                            continue

                        influx_name = rules.get("influx_field_name", "value")
                        
                        if influx_name == "value":
                            final_key_name = sensor_name
                        else:
                            final_key_name = influx_name

                        target_type = rules.get("type", "str")
                        final_val = raw_val

                        try:
                            if target_type == "int":
                                final_val = int(float(raw_val))
                            elif target_type == "float":
                                final_val = float(raw_val)
                            elif target_type == "str":
                                final_val = str(raw_val)
                        except (ValueError, TypeError) as e:
                            logging.warning(f"Type conversion for '{final_key_name}' failed (value: {raw_val}): {e}. Storing as string.")
                            final_val = str(raw_val)

                        collected_fields[final_key_name] = final_val
                        logging.debug(f"Collected field: '{final_key_name}' = {final_val} (Type: {target_type})")

            if collected_fields:
                point = {
                    "measurement": measure_name,
                    "fields": collected_fields
                }
                if timestamp_to_use:
                    point["time"] = timestamp_to_use
                
                points_batch.append(point)
                logging.debug(f"Prepared point for batch: {json.dumps(point)}")

        # 6. Write to InfluxDB
        if points_batch:
            try:
                client.write_points(points_batch)
                logging.info(f"Success: Wrote {len(points_batch)} records to InfluxDB for {data_url}.")
            except Exception as e:
                logging.error(f"InfluxDB write error for {data_url}: {e}")
        else:
            logging.info(f"No valid data points found to write for {data_url}.")

    if urls_processed == 0:
        logging.error("No 'ebusd_url_n' found or all are empty in config file.")

if __name__ == "__main__":
    fetch_and_write()