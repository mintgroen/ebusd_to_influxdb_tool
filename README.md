# ebus_tools

A collection of Python scripts to extract data from an eBUS daemon, generate a schema, and push the data to an InfluxDB time-series database.

This is useful for monitoring and visualizing data from your heating system or other eBUS-connected devices.

## How it works

The process is divided into three main steps:

1.  **Generate a Schema:** The `json_schema_generator.py` script connects to one or more eBUS daemon URLs (defined in the config), fetches all available data points, and merges them to create a single schema file (`data/ebusd_data.json`). This schema defines which data points you want to monitor and how they should be structured.
2.  **Fetch Data:** The `ebus_http_request_to_json.py` script is a utility to fetch raw JSON data from one or more eBUS daemon URLs. For each URL, it saves the output to a corresponding `data/ebusd_xxxx.json` file, where `xxxx` is the main root key of the JSON response. This is useful for debugging and inspecting the data.
3.  **Push to InfluxDB:** The `request_json_output_to_influx.py` script is the main workhorse. It fetches the latest data from all configured eBUS daemon URLs, filters and processes the data according to the generated schema, and writes the selected data points to your InfluxDB database.

## Files

*   `ebus_http_request_to_json.py`: Fetches raw JSON data from the eBUS daemon(s).
*   `json_schema_generator.py`: Generates a schema file from the eBUS data.
*   `request_json_output_to_influx.py`: Fetches, processes, and pushes data to InfluxDB.
*   `data/config.json`: The main configuration file. This is where you define eBUS URLs and InfluxDB credentials. **This file is not in the repository and must be created by you.**
*   `example data/config.json.example`: An example configuration file. You should copy this to `data/config.json` and edit it.
*   `data/ebusd_data.json`: The generated schema file (not included in the repository by default).
*   `example data/`: This folder contains example files.

## Usage

### 1. Prerequisites

*   Python 3
*   The `requests` and `influxdb-python` Python libraries. You can install them using pip:

    ```bash
    pip install requests influxdb
    ```

*   An eBUS daemon with the HTTP interface enabled.
*   An InfluxDB instance.

### 2. Configuration

1.  **Create your configuration file:**
    *   Copy `example data/config.json.example` to `data/config.json`.
    *   Edit `data/config.json` with your specific settings.
    *   You can define up to 4 URLs for fetching data and generating schemas (`schema_data_url_1` to `schema_data_url_4`, and `ebusd_url_1` to `ebusd_url_4`). The scripts will iterate through them and process any that are not empty.
    *   Fill in the details for your InfluxDB instance (`host`, `port`, `user`, `pass`, `db`).

2.  **Generate the schema:**
    *   Once your `data/config.json` is configured with at least one `schema_data_url_n`, run the schema generator:
        ```bash
        python json_schema_generator.py
        ```
    *   This will create a `data/ebusd_data.json` file. You can edit this file to enable/disable specific sensors or change the field names that will be stored in InfluxDB.

### 3. Running the scripts

*   To fetch data and store it in JSON files for debugging:
    ```bash
    python ebus_http_request_to_json.py
    ```
*   To start pushing data to InfluxDB (the main purpose of these tools):
    ```bash
    python request_json_output_to_influx.py
    ```

You can run the `request_json_output_to_influx.py` script periodically (e.g., using a cron job) to continuously monitor your eBUS data.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.