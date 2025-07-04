import streamlit as st
from utils.collections.create import (
	get_supported_vectorizers,
	validate_file_format,
	create_collection,
	create_collection_with_properties,
	get_available_data_types,
	batch_upload,
	get_collection_info,
	get_collection_objects
)
from utils.page_config import set_custom_page_config
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels

# initialize session state
def initialize_session_state():
	print("initialize_session_state() called")
	if 'collection_info' not in st.session_state:
		st.session_state.collection_info = None
	if 'custom_properties' not in st.session_state:
		st.session_state.custom_properties = []

# Function to manage dynamic property configuration
def manage_custom_properties():
	"""UI for managing custom properties dynamically"""
	st.subheader("🔧 Custom Properties Configuration")
	st.markdown("Define custom properties for your collection. These will be added to the default schema.")
	
	# Help information
	with st.expander("ℹ️ About Custom Properties", expanded=False):
		st.markdown("""
		**Custom Properties** allow you to define additional fields for your collection beyond the default schema.
		
		**Supported Data Types:**
		- **TEXT**: String values (e.g., names, descriptions)
		- **INT**: Integer numbers (e.g., age, count)
		- **NUMBER**: Decimal numbers (e.g., price, rating)
		- **BOOL**: True/False values
		- **DATE**: Date and time values
		- **UUID**: Unique identifiers
		- **BLOB**: Binary data (images, files)
		- **GEO_COORDINATES**: Geographic coordinates
		- **PHONE_NUMBER**: Phone number format
		
		**Note**: Property names will be automatically sanitized to follow Weaviate naming conventions.
		""")
	
	# Add new property section
	with st.expander("➕ Add New Property", expanded=len(st.session_state.custom_properties) == 0):
		col1, col2, col3 = st.columns([2, 2, 1])
		
		with col1:
			new_prop_name = st.text_input(
				"Property Name",
				placeholder="e.g., title, description, price",
				key="new_prop_name",
				help="Property name will be sanitized to follow Weaviate naming conventions"
			)
		
		with col2:
			new_prop_type = st.selectbox(
				"Data Type",
				options=get_available_data_types(),
				key="new_prop_type",
				help="Choose the appropriate data type for this property"
			)
		
		with col3:
			st.markdown("<br>", unsafe_allow_html=True)  # Spacing
			if st.button("Add Property", type="primary", use_container_width=True):
				if new_prop_name.strip():
					# Check for duplicate names
					sanitized_name = new_prop_name.strip().lower().replace(' ', '_')
					existing_names = [prop['name'].lower() for prop in st.session_state.custom_properties]
					
					if sanitized_name not in existing_names:
						st.session_state.custom_properties.append({
							'name': new_prop_name.strip(),
							'type': new_prop_type,
							'description': ''
						})
						st.success(f"Added property: {new_prop_name.strip()}")
						st.rerun()
					else:
						st.error("Property name already exists!")
				else:
					st.error("Please enter a property name")
	
	# Optional description for the new property
	if st.session_state.get('new_prop_name'):
		new_prop_description = st.text_area(
			"Property Description (Optional)",
			placeholder="Describe what this property represents",
			key="new_prop_description",
			height=80
		)
	
	# Display existing properties
	if st.session_state.custom_properties:
		st.markdown("**Current Properties:**")
		for i, prop in enumerate(st.session_state.custom_properties):
			col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
			
			with col1:
				st.text_input(
					f"Name {i+1}",
					value=prop['name'],
					key=f"prop_name_{i}",
					on_change=lambda i=i: update_property(i, 'name', st.session_state[f"prop_name_{i}"]),
					disabled=True  # Prevent editing to avoid key conflicts
				)
			
			with col2:
				st.selectbox(
					f"Type {i+1}",
					options=get_available_data_types(),
					index=get_available_data_types().index(prop['type']),
					key=f"prop_type_{i}",
					on_change=lambda i=i: update_property(i, 'type', st.session_state[f"prop_type_{i}"])
				)
			
			with col3:
				st.text_input(
					f"Description {i+1}",
					value=prop.get('description', ''),
					placeholder="Optional description",
					key=f"prop_desc_{i}",
					on_change=lambda i=i: update_property(i, 'description', st.session_state[f"prop_desc_{i}"])
				)
			
			with col4:
				st.markdown("<br>", unsafe_allow_html=True)  # Spacing
				if st.button("🗑️", key=f"delete_{i}", help="Delete this property"):
					st.session_state.custom_properties.pop(i)
					st.rerun()
	
		# Action buttons
		col1, col2 = st.columns(2)
		with col1:
			if st.button("🗑️ Clear All Properties", type="secondary", use_container_width=True):
				st.session_state.custom_properties = []
				st.rerun()
		with col2:
			if st.button("📋 Export Properties", type="secondary", use_container_width=True, help="Copy properties as JSON"):
				import json
				properties_json = json.dumps(st.session_state.custom_properties, indent=2)
				st.code(properties_json, language="json")
	else:
		st.info("No custom properties defined. Add properties above to customize your collection schema.")
	
	# Quick reset button (always visible)
	if st.session_state.custom_properties:
		if st.button("🔄 Reset All Properties", key="reset_all", help="Clear all custom properties"):
			st.session_state.custom_properties = []
			st.rerun()

# Helper function to update property values
def update_property(index: int, field: str, value: str):
	"""Update a specific field of a property"""
	if 0 <= index < len(st.session_state.custom_properties):
		st.session_state.custom_properties[index][field] = value

# Create a form for collection creation
def create_collection_form():
	print("create_collection_form() called")
	
	# Step 1: Collection Basic Configuration
	st.subheader("📝 Collection Configuration")
	with st.form("collection_basic_form"):
		# Collection name input
		collection_name = st.text_input(
			"Collection Name", 
			placeholder="Enter collection name",
			help="Choose a descriptive name for your collection"
		).strip()

		# Vectorizer selection
		vectorizers = get_supported_vectorizers()
		selected_vectorizer = st.selectbox(
			"Select Vectorizer",
			options=vectorizers,
			help="Choose a vectorizer for the collection. Select 'BYOV' if you plan to upload vectors manually."
		)
		
		# Show warnings for missing API keys
		if selected_vectorizer == "text2vec_openai" and not st.session_state.get("active_openai_key"):
			st.warning("⚠️ OpenAI API key is required. Please reconnect with the key or select BYOV.")
		elif selected_vectorizer == "text2vec_cohere" and not st.session_state.get("active_cohere_key"):
			st.warning("⚠️ Cohere API key is required for text2vec_cohere. Please reconnect with the key or select BYOV.")
		elif selected_vectorizer == "text2vec_jinaai" and not st.session_state.get("active_jinaai_key"):
			st.warning("⚠️ JinaAI API key is required. Please reconnect with the key or select BYOV.")
		elif selected_vectorizer == "text2vec_huggingface" and not st.session_state.get("active_huggingface_key"):
			st.warning("⚠️ HuggingFace API key is required. Please reconnect with the key or select BYOV.")
		elif selected_vectorizer == "multi2vec_clip":
			st.info("ℹ️ **Multi2vec-CLIP (Multimodal)**: Creates collections for multimodal data (text + images). Requires Weaviate instance with multi2vec-clip module enabled.")
		
		# Store basic config in session state
		if st.form_submit_button("Configure Properties", type="primary"):
			if collection_name:
				st.session_state.temp_collection_name = collection_name
				st.session_state.temp_vectorizer = selected_vectorizer
				st.session_state.show_properties_config = True
				st.rerun()
			else:
				st.error("Please enter a collection name")
	
	# Step 2: Custom Properties Configuration (only show if basic config is set)
	if st.session_state.get('show_properties_config'):
		st.divider()
		manage_custom_properties()
		
		st.divider()
		
		# Step 3: Final Collection Creation
		st.subheader("🚀 Create Collection")
		
		# Display configuration summary
		col1, col2 = st.columns(2)
		with col1:
			st.markdown(f"**Collection Name:** {st.session_state.get('temp_collection_name', 'Not set')}")
		with col2:
			st.markdown(f"**Vectorizer:** {st.session_state.get('temp_vectorizer', 'Not set')}")
		
		if st.session_state.custom_properties:
			st.markdown("**📋 Custom Properties:**")
			for prop in st.session_state.custom_properties:
				st.markdown(f"• **{prop['name']}** ({prop['type']})" + (f" - {prop['description']}" if prop.get('description') else ""))
		else:
			st.info("ℹ️ No custom properties defined. The collection will use default schema only.")
		
		# Final creation buttons
		col1, col2 = st.columns(2)
		with col1:
			if st.button("🔄 Reset Configuration", use_container_width=True):
				st.session_state.show_properties_config = False
				st.session_state.custom_properties = []
				if 'temp_collection_name' in st.session_state:
					del st.session_state.temp_collection_name
				if 'temp_vectorizer' in st.session_state:
					del st.session_state.temp_vectorizer
				st.rerun()
				
		with col2:
			create_button = st.button("✨ Create Collection", type="primary", use_container_width=True)
			
		return create_button, st.session_state.get('temp_collection_name'), st.session_state.get('temp_vectorizer')
	
	return False, None, None

# Helper function to check required API keys
def check_required_api_key(selected_vectorizer):
	if selected_vectorizer == "text2vec_openai" and not st.session_state.get("active_openai_key"):
		st.error("⚠️ OpenAI API key is required. Please reconnect with the key or select BYOV.")
		return False
	elif selected_vectorizer == "text2vec_cohere" and not st.session_state.get("active_cohere_key"):
		st.error("⚠️ Cohere API key is required for text2vec_cohere. Please reconnect with the key or select BYOV.")
		return False
	elif selected_vectorizer == "text2vec_jinaai" and not st.session_state.get("active_jinaai_key"):
		st.error("⚠️ JinaAI API key is required. Please reconnect with the key or select BYOV.")
		return False
	elif selected_vectorizer == "text2vec_huggingface" and not st.session_state.get("active_huggingface_key"):
		st.error("⚠️ HuggingFace API key is required. Please reconnect with the key or select BYOV.")
		return False
	return True

# Handle form submission
def handle_form_submission(collection_name, selected_vectorizer):
	print("handle_form_submission() called")
	print(f"Collection: {collection_name}, Vectorizer: {selected_vectorizer}")
	
	# Validate inputs
	if not collection_name:
		st.error("Please enter a collection name.")
		return
	
	# Check for required API keys
	if not check_required_api_key(selected_vectorizer):
		return
	
	try:
		# Create collection with custom properties if defined
		if st.session_state.get('custom_properties'):
			success, message = create_collection_with_properties(
				st.session_state.client, 
				collection_name, 
				selected_vectorizer,
				st.session_state.custom_properties
			)
		else:
			success, message = create_collection(
				st.session_state.client, 
				collection_name, 
				selected_vectorizer
			)
		
		if success:
			st.success(f"✅ Collection '{collection_name}' created successfully!")
			
			# Clear session state after successful creation
			st.session_state.show_properties_config = False
			if st.session_state.get('custom_properties'):
				st.session_state.custom_properties = []
				st.info("🧹 Custom properties cleared for next collection.")
			
			# Clear temporary session state
			if 'temp_collection_name' in st.session_state:
				del st.session_state.temp_collection_name
			if 'temp_vectorizer' in st.session_state:
				del st.session_state.temp_vectorizer
				
			# Get collection info
			success, info_msg, collection_info = get_collection_info(st.session_state.client, collection_name)
			if success:
				st.session_state.collection_info = collection_info
			else:
				st.error(info_msg)
			
			st.info("💡 Your collection is now ready! You can add data to it using the 'Upload Data' page or through the API.")
		else:
			st.error(f"❌ Failed to create collection: {message}")
		
	except Exception as e:
		st.error(f"❌ An error occurred: {str(e)}")
		print(f"Error in handle_form_submission: {e}")


# Function to display collection information
def display_collection_info(client):
	print("display_collection_info() called")
	if not st.session_state.collection_info:
		return

	info = st.session_state.collection_info

	# Button to view objects
	if st.button("View Collection (100 Objects only)", use_container_width=True):
		# Display only Object Count
		st.metric("Object Count", info["object_count"])

		# Then display the objects
		success, msg, df = get_collection_objects(client, info["name"])
		if success:
			st.dataframe(df)
		else: 
			st.error(msg)

def main():

	set_custom_page_config(page_title="Create Collection")

	navigate()

	if st.session_state.get("client_ready"):
		update_side_bar_labels()
		initialize_session_state()
		client = st.session_state.client
		create_button, collection_name, selected_vectorizer = create_collection_form()
		if create_button:
			handle_form_submission(collection_name, selected_vectorizer)
		display_collection_info(client)

	else:
		st.warning("Please Establish a connection to Weaviate in Cluster page!")

if __name__ == "__main__":
	main()
