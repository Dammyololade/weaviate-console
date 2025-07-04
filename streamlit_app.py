import streamlit as st
from utils.connection.weaviate_client import initialize_client
from utils.cluster.cluster_operations_handlers import action_check_shard_consistency, action_aggregate_collections_tenants, action_collections_configuration, action_metadata, action_nodes_and_shards, action_collection_schema, action_statistics, action_read_repairs
from utils.sidebar.navigation import navigate
from utils.connection.weaviate_connection import close_weaviate_client
from utils.sidebar.helper import update_side_bar_labels, clear_session_state
from utils.page_config import set_custom_page_config
from pages.connections import initialize_connection_session_state
import time

# --------------------------------------------------------------------------
# Initialize session state
# --------------------------------------------------------------------------
if "client_ready" not in st.session_state:
	st.session_state.client_ready = False

# Active connection state
if "active_endpoint" not in st.session_state:
	st.session_state.active_endpoint = ""
if "active_api_key" not in st.session_state:
	st.session_state.active_api_key = ""

# Initialize connection session state
initialize_connection_session_state()

# ------------------------ß--------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------------------------------

# Use with default page title
set_custom_page_config()

# --------------------------------------------------------------------------
# Navigation on side bar
# --------------------------------------------------------------------------
navigate()




# Essential run for the first time
update_side_bar_labels()

# --------------------------------------------------------------------------
# Main Page Content (Cluster Operations)
# --------------------------------------------------------------------------
st.markdown("###### ⚠️ Important: This tool is designed and tested on the latest Weaviate DB version. Some features may not be compatible with older versions. Please ensure you are using the latest stable version of Weaviate DB for optimal performance.")
st.markdown("###### Any function with (APIs) means it is run using RESTful endpoints. Otherwise, it is executed through the DB client.")
# --------------------------------------------------------------------------
# Buttons (calls a function)
# --------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 1, 1])
col4, col5, col6 = st.columns([1, 1, 1])
col7, col8 = st.columns([1,1])

# Dictionary: button name => action function
button_actions = {
	"nodes": action_nodes_and_shards,
	"aggregate_collections_tenants": action_aggregate_collections_tenants,
	"collection_properties": action_collection_schema,
	"collections_configuration": lambda: action_collections_configuration(st.session_state.active_endpoint, st.session_state.active_api_key),
	"statistics": lambda: action_statistics(st.session_state.active_endpoint, st.session_state.active_api_key),
	"metadata": lambda: action_metadata(st.session_state.active_endpoint, st.session_state.active_api_key),
	"check_shard_consistency": action_check_shard_consistency,
	"read_repairs": lambda: action_read_repairs(st.session_state.active_endpoint, st.session_state.active_api_key),
}

with col1:
	if st.button("Aggregate Collections & Tenants", use_container_width=True):
		st.session_state["active_button"] = "aggregate_collections_tenants"

with col2:
	if st.button("Collection Properties", use_container_width=True):
		st.session_state["active_button"] = "collection_properties"

with col3:
	if st.button("Collections Configuration (APIs)", use_container_width=True):
		st.session_state["active_button"] = "collections_configuration"

with col4:
	if st.button("Nodes & Shards", use_container_width=True):
		st.session_state["active_button"] = "nodes"

with col5:
	if st.button("Raft Statistics (APIs)", use_container_width=True):
		st.session_state["active_button"] = "statistics"

with col6:
	if st.button("Metadata",use_container_width=True):
		st.session_state["active_button"] = "metadata"

with col7:
	if st.button("Check Shard Consistency For Repairs", use_container_width=True):
		st.session_state["active_button"] = "check_shard_consistency"

with col8:
	if st.button("Read Repair (APIs)", use_container_width=True):
		st.session_state["active_button"] = "read_repairs"

# --------------------------------------------------------------------------
# Execute the active button's action
# --------------------------------------------------------------------------
active_button = st.session_state.get("active_button")
if active_button and st.session_state.get("client_ready"):
	action_fn = button_actions.get(active_button)
	if action_fn:
		action_fn()
	else:
		st.warning("No action mapped for this button. Please report this issue to Mohamed Shahin in Weaviate Community Slack.")
elif not st.session_state.get("client_ready"):
	st.warning("Connect to Weaviate first!")
