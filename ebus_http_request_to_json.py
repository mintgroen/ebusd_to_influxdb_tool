import requests
import json
import os

# --- Configuration ---
CONFIG_FILE = "data/config.json"
OUTPUT_DIR = "data"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load Configuration ---
config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    print(f"Error: Config file not found at {CONFIG_FILE}")
    exit(1)

# Get URLs and Timeout from config
ebus_config = config.get("ebusd", {})
ebusd_http_timeout = ebus_config.get("ebusd_http_timeout", 60)

urls_processed = 0
for i in range(1, 5):
    url = ebus_config.get(f"ebusd_url_{i}")
    if not url:
        continue

    urls_processed += 1
    try:
        # 1. Send the HTTP GET request
        print(f"Fetching data from {url} with a timeout of {ebusd_http_timeout} seconds...")
        response = requests.get(url, timeout=ebusd_http_timeout)
        
        # 2. Check if the request was successful (Status Code 200)
        response.raise_for_status()

        # 3. Parse the response content as JSON
        data = response.json()

        # 4. Determine output filename
        if not data or not isinstance(data, dict) or len(data.keys()) != 1:
            print(f"Warning: JSON response from {url} is not a dictionary with a single root key. Skipping file generation.")
            continue
        
        root_key = list(data.keys())[0]
        output_file = os.path.join(OUTPUT_DIR, f"ebusd_{root_key}.json")

        # 5. Write the data to a file
        with open(output_file, 'w', encoding='utf-8') as f:
            # indent=4 makes the file readable (pretty printed)
            json.dump(data, f, indent=4) 

        print(f"Success! Data saved to {output_file}")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for {url}: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred for {url}: {conn_err}")
    except json.JSONDecodeError:
        print(f"Error: The response from {url} was not valid JSON.")
    except Exception as err:
        print(f"An unexpected error occurred for {url}: {err}")

if urls_processed == 0:
    print("Error: No 'ebusd_url_n' found or all are empty in config file.")
    exit(1)
