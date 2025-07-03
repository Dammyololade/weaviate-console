import streamlit as st
from utils.collections.create import (
	get_supported_vectorizers,
	validate_file_format,
	create_collection,
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

# Create a form for collection creation
def create_collection_form():
	print("create_collection_form() called")
	with st.form("create_collection_form"):
		# Collection name input
		collection_name = st.text_input("Collection Name", placeholder="Enter collection name").strip()

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
			st.info("ℹ️ **Multi2vec-CLIP (Multimodal)**: Creates collections with predefined schema for text (title, description) and image (blob) fields. Requires Weaviate instance with multi2vec-clip module enabled and CLIP inference container running. No API key required - uses local inference.")
			st.warning("⚠️ **Important**: Provide title and description below, plus upload an image file that the model will embed alongside the text.")

		# Multi2vec-CLIP specific inputs
		title = None
		description = None
		if selected_vectorizer == "multi2vec_clip":
			st.subheader("📝 Content for Multi2vec-CLIP")
			title = st.text_input(
				"Title",
				placeholder="Enter a title for your content",
				help="This will be used as the title field for the multimodal embedding"
			).strip()
			description = st.text_area(
				"Description",
				placeholder="Enter a description for your content",
				help="This will be used as the description field for the multimodal embedding",
				height=100
			).strip()

		# File upload
		file_help_text = "Upload a CSV or JSON file containing your data"
		file_label = "Upload .csv or .json Data File"
		file_types = ["csv", "json"]
		
		if selected_vectorizer == "multi2vec_clip":
			file_help_text = "Upload an image file that will be embedded alongside the title and description"
			file_label = "Upload Image File"
			file_types = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]

		uploaded_file = st.file_uploader(
			file_label,
			type=file_types,
			help=file_help_text
		)

		# Submit button
		submit_button_text = "Create Collection and Upload Data"
		if selected_vectorizer == "multi2vec_clip":
			submit_button_text = "Create Collection and Embed Content"
		
		submit_button = st.form_submit_button(submit_button_text)

		return submit_button, collection_name, selected_vectorizer, uploaded_file, title, description

# Handle form submission
def handle_form_submission(client, collection_name, selected_vectorizer, uploaded_file, title=None, description=None):
	print("handle_form_submission() called")
	if not collection_name:
		st.error("Please enter a collection name")
		return
	
	# Validation for multi2vec-clip
	if selected_vectorizer == "multi2vec_clip":
		if not title or not description:
			st.error("Please provide both title and description for Multi2vec-CLIP")
			return
		if not uploaded_file:
			st.error("Please upload an image file for Multi2vec-CLIP")
			return
	else:
		if not uploaded_file:
			st.error("Please upload a data file")
			return

	# Create collection
	success, message = create_collection(client, collection_name, selected_vectorizer)
	if not success:
		st.error(message)
		return

	st.success(message)

	# Handle data processing based on vectorizer type
	if selected_vectorizer == "multi2vec_clip":
		# For multi2vec-clip, create data from form inputs
		import base64
		
		# Convert image to base64
		image_bytes = uploaded_file.getvalue()
		image_base64 = base64.b64encode(image_bytes).decode('utf-8')
		
		# Create data structure for multi2vec-clip
		data = [{
			"title": title,
			"description": description,
			"image": image_base64
		}]
	else:
		# Read and validate file for other vectorizers
		file_content = uploaded_file.getvalue().decode('utf-8')
		file_type = uploaded_file.name.split('.')[-1].lower()

		is_valid, validation_msg, data = validate_file_format(file_content, file_type)
		if not is_valid:
			st.error(f"File validation failed: {validation_msg}") 
			return

	# Create a placeholder for progress updates
	progress_placeholder = st.empty()

	progress_messages = []

	# Process the batch upload generator
	for success, message, _ in batch_upload(client, collection_name, data):
		progress_messages.append(message)
		# Update progress display with HTML scrollable div on each yield
		html_content = f"""
		                <div style="
		                	height: 300px;
		                	overflow-y: auto;
		                	border: 1px solid #ccc;
		                	padding: 10px;
		                ">
		                {"<br>".join(progress_messages)}
		                </div>
		                """
		progress_placeholder.markdown(html_content, unsafe_allow_html=True)

	# After the loop finishes, the last message should indicate completion status
	# The detailed failed objects will be printed to the terminal

	# Get collection info
	success, info_msg, collection_info = get_collection_info(client, collection_name)
	if success:
		st.session_state.collection_info = collection_info
	else:
		st.error(info_msg)


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
		submit_button, collection_name, selected_vectorizer, uploaded_file, title, description = create_collection_form()
		if submit_button:
			handle_form_submission(client, collection_name, selected_vectorizer, uploaded_file, title, description)
		display_collection_info(client)

	else:
		st.warning("Please Establish a connection to Weaviate in Cluster page!")

if __name__ == "__main__":
	main()
