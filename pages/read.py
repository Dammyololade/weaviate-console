import streamlit as st
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels
from utils.collections.read_all_objects import list_all_collections, get_tenant_names, fetch_collection_data
from utils.page_config import set_custom_page_config

def main():
	set_custom_page_config(page_title="Read Collections")
	navigate()

	if st.session_state.get("client_ready"):
		update_side_bar_labels()
		client = st.session_state.client

		# Initialize session state variables
		if "collections_list" not in st.session_state:
			st.session_state.collections_list = []
		if "query_results" not in st.session_state:
			st.session_state.query_results = None
		if "current_collection" not in st.session_state:
			st.session_state.current_collection = None
		if "current_tenant" not in st.session_state:
			st.session_state.current_tenant = None
		if "current_page" not in st.session_state:
			st.session_state.current_page = 1
		if "items_per_page" not in st.session_state:
			st.session_state.items_per_page = 1000

		# Refresh button to load collections
		if st.button("Load Collections List",type="primary", use_container_width=True):
			collections = list_all_collections(client)
			if not isinstance(collections, list):
				collections = list(collections.keys())
			collections.sort()
			st.session_state.collections_list = collections
			st.session_state.query_results = None
			st.session_state.current_collection = None
			st.session_state.current_tenant = None
			st.session_state.current_page = 1
			st.rerun()

		# Only show collection selection if we have collections
		if st.session_state.collections_list:
			# Collection selection
			selected_collection = st.selectbox(
				"Select a Collection",
				st.session_state.collections_list,
				key="main_collection_select"
			)

			# Get and sort tenant names
			tenant_names = get_tenant_names(client, selected_collection)
			if tenant_names:
				tenant_names = sorted(tenant_names)

			selected_tenant = None
			if tenant_names:
				selected_tenant = st.selectbox(
					"Select a Tenant",
					tenant_names,
					key="main_tenant_select"
				)

			# Add pagination controls
			col1, col2 = st.columns([2, 1])
			with col1:
				items_per_page = st.selectbox(
					"Items per page",
					options=[100, 500, 1000, 2000, 5000],
					index=[100, 500, 1000, 2000, 5000].index(st.session_state.items_per_page),
					key="items_per_page_select"
				)
				if items_per_page != st.session_state.items_per_page:
					st.session_state.items_per_page = items_per_page
					st.session_state.query_results = None

			# Check if we need to reset the results
			if (st.session_state.current_collection != selected_collection or 
				st.session_state.current_tenant != selected_tenant):
				st.session_state.query_results = None
				st.session_state.current_page = 1

			read_button = st.button("Read Objects", use_container_width=True)

			# Fetch data
			if read_button or st.session_state.query_results is not None:
				if tenant_names and not selected_tenant:
					st.error("Please select a tenant for this collection")
				else:
					# Only fetch new data if we don't have results or if Read Objects was clicked
					if read_button or st.session_state.query_results is None:
						with st.spinner("Fetching objects with pagination... ⤵️"):
							result = fetch_collection_data(
								client, 
								selected_collection, 
								selected_tenant, 
								page=st.session_state.current_page,
								items_per_page=st.session_state.items_per_page
							)
							st.session_state.query_results = result
							st.session_state.current_collection = selected_collection
							st.session_state.current_tenant = selected_tenant

					result = st.session_state.query_results

					if not result["data"].empty:
						# Display pagination info
						st.info(f"Showing page {result['current_page']} of {result['total_pages']} " +
							f"(Total items: {result['total_count']})")

						# Display the data
						st.dataframe(result["data"].astype(str), use_container_width=True)

						# Pagination controls
						col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

						with col1:
							if st.button("⏮️ First", disabled=st.session_state.current_page == 1):
								st.session_state.current_page = 1
								st.session_state.query_results = fetch_collection_data(
									client, selected_collection, selected_tenant,
									page=1, items_per_page=st.session_state.items_per_page
								)
								st.rerun()

						with col2:
							if st.button("◀️ Previous", disabled=st.session_state.current_page == 1):
								st.session_state.current_page -= 1
								st.session_state.query_results = fetch_collection_data(
									client, selected_collection, selected_tenant,
									page=st.session_state.current_page, items_per_page=st.session_state.items_per_page
								)
								st.rerun()

						with col3:
							if st.button("Next ▶️", disabled=st.session_state.current_page >= result["total_pages"]):
								st.session_state.current_page += 1
								st.session_state.query_results = fetch_collection_data(
									client, selected_collection, selected_tenant,
									page=st.session_state.current_page, items_per_page=st.session_state.items_per_page
								)
								st.rerun()

						with col4:
							if st.button("Last ⏭️", disabled=st.session_state.current_page >= result["total_pages"]):
								st.session_state.current_page = result["total_pages"]
								st.session_state.query_results = fetch_collection_data(
									client, selected_collection, selected_tenant,
									page=st.session_state.current_page, items_per_page=st.session_state.items_per_page
								)
								st.rerun()

						# Page number input
						page_number = st.number_input(
							f"Go to page (1-{result['total_pages']})",
							min_value=1,
							max_value=result["total_pages"],
							value=st.session_state.current_page
						)

						if page_number != st.session_state.current_page:
							st.session_state.current_page = page_number
							st.session_state.query_results = fetch_collection_data(
								client, selected_collection, selected_tenant,
								page=page_number, items_per_page=st.session_state.items_per_page
							)
							st.rerun()

					else:
						st.warning("No data found")
		else:
			st.info("Load available collections...")
	else:
		st.warning("Please Establish a connection to Weaviate in Cluster page!")

if __name__ == "__main__":
	main()
