import requests
import datetime
from influxdb import InfluxDBClient

# --- Configuration ---
DATA_URL = "http://ebusdeamon-ip-adress:8889/data?maxage=60"

# InfluxDB 1.x Settings
INFLUX_HOST = "influxdb-ip-adress"
INFLUX_PORT = 8086
INFLUX_USER = "username"
INFLUX_PASS = "password"
INFLUX_DB   = "test-database"

def fetch_and_write():
    print("--- STARTING SCRIPT ---")

    # 1. Fetch JSON Data
    print(f"\n[Step 1] Requesting data from: {DATA_URL}")
    try:
        response = requests.get(DATA_URL, timeout=60)
        response.raise_for_status()
        data = response.json()
        print(f" -> JSON parsed successfully.")
    except Exception as e:
        print(f"![ERROR] Could not fetch data: {e}")
        return

    # 2. Prepare InfluxDB Client
    print(f"\n[Step 2] Connecting to InfluxDB at {INFLUX_HOST}:{INFLUX_PORT}")
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, 
                            username=INFLUX_USER, password=INFLUX_PASS, 
                            database=INFLUX_DB)
    
    # 3. Parse JSON and Aggregate
    points_batch = []

    for measurement_name, measurement_data in data.items():
        
        # Check if the root item is a dict and has "messages"
        if not isinstance(measurement_data, dict) or "messages" not in measurement_data:
            print(f" -> Skipping root key '{measurement_name}' (No 'messages' found).")
            continue

        print(f"\n[Step 3] Processing Root Key: '{measurement_name}'")
        
        messages = measurement_data["messages"]
        
        # --- FIX: Check if 'messages' is actually a dictionary ---
        if not isinstance(messages, dict):
            print(f" -> Skipping '{measurement_name}': 'messages' is not a dictionary (Type: {type(messages).__name__})")
            continue
        # ---------------------------------------------------------

        collected_fields = {}
        timestamp_to_use = None

        for sensor_name, sensor_data in messages.items():
            
            # --- FIX: Ensure sensor_data is a dictionary ---
            # If 'sensor_data' is just a number (e.g. "count": 5), we can't look for .get("fields") inside it.
            if not isinstance(sensor_data, dict):
                 print(f"    [Skip] '{sensor_name}' is not a complex object (Type: {type(sensor_data).__name__})")
                 continue
            # -----------------------------------------------

            # A. Capture Timestamp
            if timestamp_to_use is None and "lastup" in sensor_data:
                raw_time = sensor_data["lastup"]
                try:
                    timestamp_to_use = datetime.datetime.utcfromtimestamp(raw_time).strftime('%Y-%m-%dT%H:%M:%SZ')
                    print(f"    [Timestamp] Locked in time: {timestamp_to_use}")
                except (ValueError, TypeError):
                    pass # unexpected timestamp format

            # B. Capture Value (Smart Datatype Retention)
            try:
                inner_fields = sensor_data.get("fields", {})
                
                # Check if inner_fields is actually a dict
                if inner_fields and isinstance(inner_fields, dict):
                    first_inner_key = next(iter(inner_fields)) 
                    # We also need to check if the inner item is a dict before calling .get()
                    inner_obj = inner_fields[first_inner_key]
                    
                    if isinstance(inner_obj, dict):
                        raw_val = inner_obj.get("value")
                    
                        if raw_val is not None:
                            final_val = raw_val
                            
                            # Smart Type Detection
                            if isinstance(raw_val, str):
                                try:
                                    final_val = int(raw_val)
                                except ValueError:
                                    try:
                                        final_val = float(raw_val)
                                    except ValueError:
                                        final_val = raw_val

                            collected_fields[sensor_name] = final_val
                            print(f"    [Field] {sensor_name} = {final_val} (Type: {type(final_val).__name__})")

            except Exception as e:
                print(f"    [Error] Processing '{sensor_name}': {e}")
                continue

        # 4. Construct Point
        if collected_fields:
            point = {
                "measurement": measurement_name,
                "fields": collected_fields
            }
            if timestamp_to_use:
                point["time"] = timestamp_to_use
            
            points_batch.append(point)

    # 5. Write to DB
    print("\n[Step 4] Writing batch to Database...")
    if points_batch:
        try:
            client.write_points(points_batch)
            print(f" -> SUCCESS! Written {len(points_batch)} point(s).")
        except Exception as e:
            print(f"![ERROR] InfluxDB Write Failed: {e}")
    else:
        print(" -> Nothing to write.")

    print("\n--- SCRIPT FINISHED ---")

if __name__ == "__main__":
    fetch_and_write()
