# Weaviate Cluster Operations & Analysis 🔍

## Overview

Interact with and manage Weaviate Cluster operations. This app provides tools to inspect shards, view collections & tenants, explore schemas, analyze cluster statistics, and interact with objects.

[![Go to the WebApp](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://weaviatecluster.streamlit.app/)

## Features

- **Shards & Nodes**: View shard details across nodes as well as node details.
- **Collections & Tenants**: Aggregate and view collections and their tenants.
- **Collections Configuration**: Explore collection configurations.
- **Schema**: Fetch and view the schema configuration of your Weaviate cluster.
- **Statistics**: Analyze cluster synchronization and node statistics.
- **Metadata**: View cluster metadata & modules.
- **Consistency**: Analyze shards for inconsistency.
- **Object Operations**:
	- Fetch object data in collections.
	- Analyze consistency of an object across nodes (currently hardcoded for a max of 11 nodes).
	- Fetch object data in tenants.
- **Multi-Tenancy Operations**:
	- Visualize tenants and their states.
- **Collection Data**:
	- Read and get all your objects data from a collection/tenant in a table.
	- Download the data locally in a `.csv` file.

## Configuration

### How to Run It on Your Local Machine

**Prerequisites**

- Python 3.10 or higher
- pip installed

**Steps to Run**

1. **Clone the repository:**

   ```bash
   $ git clone https://github.com/Shah91n/ClusterInMotion.git
   $ cd ClusterInMotion
   ```

2. **Install the required dependencies:**

   ```bash
   $ pip install -r requirements.txt
   ```

3. **Run the app:**

   ```bash
   $ streamlit run streamlit_app.py
   ```


If you haven’t already created a requirements.txt file, here’s what it should look like:

```bash
streamlit
weaviate-client
requests
pandas
```

```bash
$ pip install -r requirements.txt
```

**or Open the app in your browser:**

The app will typically run at http://localhost:8501. Enabling the “Local Cluster” checkbox allows you to use a local cluster instead of a cloud one (ensure that authentication requirements are set to false in your .yaml environment file).

### How to Run It on a Cloud Cluster
1. Provide the Weaviate endpoint.
2. Provide the API key.
3. Connect and enjoy!

### Notes

This is a personal project and is not officially approved by the Weaviate organization. While functional, the code may not follow all best practices for Python programming or Streamlit. Suggestions and improvements are welcome!

USE AT YOUR OWN RISK: While this tool is designed for cluster operation and analysis, there is always a possibility of unknown bugs. However, this tool is intended for read-only operations.

### Contributing

Contributions are welcome through pull requests! Suggestions for improvements and best practices are highly appreciated.
