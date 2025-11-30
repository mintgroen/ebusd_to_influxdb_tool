import requests
import json
import collections
import os

# --- Configuration ---
CONFIG_FILE = "data/config.json"
OUTPUT_FILE = "data/ebusd_data.json"

# --- Load Configuration ---
config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    print(f"Error: Config file not found at {CONFIG_FILE}")
    exit(1)


# Lijst met generieke namen die we liever niet als veldnaam gebruiken,
# tenzij er echt niets anders is. Als een veld hierop uitkomt, gebruiken
# we de naam van de Sensor (bv. "AirInletTemp") als veldnaam.
GENERIC_KEYS = ["0", "value", "tempv", "temps2", "pressv", "cntstarts2"]

def detect_type(value):
    """Bepaalt of een waarde een int, float of str is."""
    if value is None:
        return "str"
    
    if isinstance(value, str):
        try:
            f = float(value)
            if f.is_integer():
                return "int"
            return "float"
        except ValueError:
            return "str"
    elif isinstance(value, bool):
        return "str"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    else:
        return "str"

def generate_schema():
    ebus_config = config.get("ebusd", {})
    ebusd_http_timeout = ebus_config.get("ebusd_http_timeout", 60)
    
    merged_schema = {}

    for i in range(1, 5):
        data_url = ebus_config.get(f"schema_data_url_{i}")
        if not data_url:
            continue
            
        print(f"--- GENERATING SCHEMA FROM {data_url} ---")
        
        try:
            response = requests.get(data_url, timeout=ebusd_http_timeout)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"![ERROR] Could not fetch data from {data_url}: {e}")
            continue

        # Stap 1: Loop door de root keys (zoals "hmu")
        for root_key, root_data in data.items():
            if not isinstance(root_data, dict) or "messages" not in root_data:
                continue
            
            messages = root_data["messages"]
            if not isinstance(messages, dict):
                continue

            if root_key not in merged_schema:
                merged_schema[root_key] = {}

            # Stap 2: Loop door de sensoren
            for sensor_name, sensor_data in messages.items():
                if not isinstance(sensor_data, dict):
                    continue

                inner_fields = sensor_data.get("fields", {})
                if not isinstance(inner_fields, dict):
                    continue
                
                # We houden bij welke namen we al gebruikt hebben binnen DEZE sensor
                # om dubbele namen (collisions) te voorkomen.
                used_field_names = []

                # Stap 3: Loop door alle sub-fields
                for field_key, field_data in inner_fields.items():
                    
                    # --- LOGICA VOOR NAAMBEPALING ---
                    # 1. Start met de key zelf (bv. "0" of "S00_SupplyTemp")
                    candidate_name = field_key
                    
                    # 2. Kijk of er een interne "name" beschikbaar is (bv. "pumpstate" of "temp1")
                    internal_name = field_data.get("name")
                    if internal_name and isinstance(internal_name, str) and internal_name.strip() != "":
                        candidate_name = internal_name
                    
                    # 3. Filter generieke namen
                    if candidate_name in GENERIC_KEYS:
                        final_field_name = "value"
                    else:
                        final_field_name = candidate_name

                    # 4. Uniek maken (Conflict Resolutie)
                    if final_field_name != "value":
                        original_name = final_field_name
                        counter = 1
                        while final_field_name in used_field_names:
                            final_field_name = f"{original_name}_{field_key}"
                            if final_field_name in used_field_names:
                                 final_field_name = f"{original_name}_{counter}"
                                 counter += 1
                    
                    used_field_names.append(final_field_name)
                    
                    # --- DATATYPE BEPALING ---
                    val = field_data.get("value")
                    detected_type = detect_type(val)
                    
                    # Toevoegen aan Schema
                    if sensor_name not in merged_schema[root_key]:
                        merged_schema[root_key][sensor_name] = {}

                    merged_schema[root_key][sensor_name][field_key] = {
                        "type": detected_type,
                        "enabled": True,
                        "influx_field_name": final_field_name
                    }

    # Opslaan
    if merged_schema:
        try:
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(merged_schema, f, indent=4)
            print(f"Success! Schema saved to '{OUTPUT_FILE}'.")
            print("Note: Check the file for fields like 'temp1_0' or 'temp1_1' to see if naming is correct.")
            
        except Exception as e:
            print(f"![ERROR] Could not save file: {e}")
    else:
        print("No schema generated as no data could be fetched or processed.")

if __name__ == "__main__":
    generate_schema()
