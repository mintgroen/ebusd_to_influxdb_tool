import requests
import json

# Configuration
url = "http://192.168.0.3:8889/data?maxage=60"
output_file = "output.json"

try:
    # 1. Send the HTTP GET request
    response = requests.get(url, timeout=60) # 5-second timeout is good practice
    
    # 2. Check if the request was successful (Status Code 200)
    response.raise_for_status()

    # 3. Parse the response content as JSON
    data = response.json()

    # 4. Write the data to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        # indent=4 makes the file readable (pretty printed)
        json.dump(data, f, indent=4) 

    print(f"Success! Data saved to {output_file}")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
except requests.exceptions.ConnectionError as conn_err:
    print(f"Connection error occurred: {conn_err}")
except json.JSONDecodeError:
    print("Error: The response from the server was not valid JSON.")
except Exception as err:
    print(f"An unexpected error occurred: {err}")