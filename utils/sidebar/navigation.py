import streamlit as st
from PIL import Image
import os

# This function is used to set up the sidebar navigation for the Streamlit app.
# It includes links to different pages of the app and displays the Weaviate logo.
def navigate():
	logo_path = os.path.join("assets", "weaviate-logo.png")
	logo_image = Image.open(logo_path)
	st.sidebar.image(logo_image, width=100)
	
	# Connect Button
	if st.session_state.get("client_ready"):
		col1, col2 = st.sidebar.columns(2)
		with col1:
			if st.button("ℹ️ Info", use_container_width=True, type="secondary"):
				from pages.connections import show_connection_info_dialog
				show_connection_info_dialog()
		with col2:
			if st.button("🔌 Disconnect", use_container_width=True, type="secondary"):
				from utils.connection.weaviate_connection import close_weaviate_client
				from utils.sidebar.helper import clear_session_state
				st.toast('Session, states and cache cleared! Weaviate client disconnected successfully!', icon='🔴')
				if st.session_state.get("client_ready"):
					close_weaviate_client()
					clear_session_state()
					st.rerun()
	else:
		if st.sidebar.button("🔗 Connect", use_container_width=True, type="primary"):
			from pages.connections import show_connection_dialog
			show_connection_dialog()
	
	# Settings Section
	with st.sidebar.expander("⚙️ Settings", expanded=False):
		st.page_link("streamlit_app.py", label="Cluster", icon="🔍")
		st.page_link("pages/multitenancy.py", label="Multi Tenancy", icon="📄")
		st.page_link("pages/rbac.py", label="Role-Based Access Control", icon="🔐")
	
	# Collections Section
	with st.sidebar.expander("📚 Collections", expanded=False):
		st.page_link("pages/create.py", label="Create", icon="➕")
		st.page_link("pages/read_collections.py", label="Read", icon="📖")
		st.page_link("pages/edit_collections.py", label="Edit", icon="✏️")
		st.page_link("pages/delete_collections.py", label="Delete", icon="🗑️")
	
	# Documents Section
	with st.sidebar.expander("📄 Documents", expanded=False):
		st.page_link("pages/search.py", label="Search", icon="🧐")
		st.page_link("pages/add_document.py", label="Add Document", icon="📝")
		st.page_link("pages/read.py", label="Read", icon="📁")
		st.page_link("pages/update.py", label="Update", icon="🗃️")
		st.page_link("pages/delete.py", label="Delete", icon="🗑️")
	
	# Backup Section
	with st.sidebar.expander("💾 Backup", expanded=False):
		st.page_link("pages/backup.py", label="Backup Management", icon="💾")
	
	st.sidebar.markdown("---")
