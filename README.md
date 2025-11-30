# ebus_tools

A collection of Python scripts to extract data from an eBUS daemon, generate a schema, and push the data to an InfluxDB time-series database.

This is useful for monitoring and visualizing data from your heating system or other eBUS-connected devices.

## How it works

The process is divided into three main steps:

1.  **Generate a Schema:** The `Json_schema_generator.py` script connects to your eBUS daemon, fetches all available data points, and creates a schema file (`ebusd_data.json`). This schema defines which data points you want to monitor and how they should be structured.
2.  **Fetch Data:** The `ebus_http_request_to_json.py` script is a simple utility to fetch the raw JSON data from the eBUS daemon and save it to a file (`output.json`). This is useful for debugging and inspecting the data.
3.  **Push to InfluxDB:** The `request_json_output_to_influx.py` script is the main workhorse. It fetches the latest data from the eBUS daemon, filters and processes it according to the schema you generated, and writes the selected data points to your InfluxDB database.

## Files

*   `ebus_http_request_to_json.py`: Fetches raw JSON data from the eBUS daemon.
*   `Json_schema_generator.py`: Generates a schema file from the eBUS data.
*   `request_json_output_to_influx.py`: Fetches, processes, and pushes data to InfluxDB.
*   `config.json`: Configuration file for the InfluxDB script (eBUS URL and InfluxDB credentials).
*   `ebusd_data.json`: The generated schema file (not included in the repository by default).
*   `output.json`: Example raw JSON output from the eBUS daemon.

## Usage

### 1. Prerequisites

*   Python 3
*   The `requests` and `influxdb` Python libraries. You can install them using pip:

    ```bash
    pip install requests influxdb
    ```

*   An eBUS daemon with the HTTP interface enabled.
*   An InfluxDB instance.

### 2. Configuration

1.  **Create the schema:**
    *   Open `Json_schema_generator.py` and change the `DATA_URL` to the URL of your eBUS daemon's data endpoint (e.g., `http://<your-ebus-ip>:8889/data/hmu?required`).
    *   Run the script:
        ```bash
        python Json_schema_generator.py
        ```
    *   This will create a `ebusd_data.json` file. You can edit this file to enable/disable specific sensors or change the field names.

2.  **Configure the InfluxDB connection:**
    *   Rename `config.json.example` to `config.json`.
    *   Edit `config.json` and fill in the details for your eBUS daemon (`data_url`) and your InfluxDB instance (`host`, `port`, `user`, `pass`, `db`).

### 3. Running the script

Once you have configured everything, you can run the main script to start pushing data to InfluxDB:

```bash
python request_json_output_to_influx.py
```

You can run this script periodically (e.g., using a cron job) to continuously monitor your eBUS data.

## Example

The `example data` folder contains an example of the raw JSON output from the eBUS daemon (`ebusd_data.json`) and the corresponding output file (`output.json`).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.