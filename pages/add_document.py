import streamlit as st
import json
import base64
from typing import Dict, Any, List, Optional
from utils.collections.create import batch_upload, sanitize_keys
from utils.collections.read_all_objects import list_all_collections
from utils.cluster.collection import get_schema
from utils.page_config import set_custom_page_config
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels
from weaviate.classes.config import DataType
import pandas as pd

# Initialize session state
def initialize_session_state():
    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = None
    if 'collection_schema' not in st.session_state:
        st.session_state.collection_schema = None
    if 'document_data' not in st.session_state:
        st.session_state.document_data = {}

# Get collection schema and properties
def get_collection_schema(client, collection_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema for a specific collection"""
    try:
        schema = get_schema(client)
        if schema and not isinstance(schema, dict) or "error" not in schema:
            # schema is a collections object, convert to dict format
            for name, collection_details in schema.items():
                if name == collection_name:
                    return {
                        "name": collection_details.name,
                        "description": collection_details.description,
                        "vectorizer": collection_details.vectorizer,
                        "properties": [{
                            "name": prop.name,
                            "description": prop.description,
                            "data_type": prop.data_type,
                            "index_searchable": prop.index_searchable,
                            "index_filterable": prop.index_filterable
                        } for prop in collection_details.properties]
                    }
        return None
    except Exception as e:
        st.error(f"Error getting collection schema: {str(e)}")
        return None

# Create dynamic form based on collection schema
def create_dynamic_form(collection_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Create a dynamic form based on collection properties"""
    st.subheader(f"Add Document to Collection: {collection_schema['name']}")
    
    if collection_schema.get('description'):
        st.info(f"Collection Description: {collection_schema['description']}")
    
    # Show vectorizer info
    vectorizer = collection_schema.get('vectorizer', 'none')
    if vectorizer == 'multi2vec_clip':
        st.success("🎯 This collection uses Multi2vec-CLIP (Multimodal) vectorizer - perfect for text and image content!")
    elif vectorizer and vectorizer != 'none':
        st.info(f"📊 Vectorizer: {vectorizer}")
    else:
        st.warning("⚠️ This collection uses BYOV (Bring Your Own Vectors) or no vectorizer")
    
    document_data = {}
    
    with st.form("add_document_form"):
        st.markdown("### Document Properties")
        
        properties = collection_schema.get('properties', [])
        if not properties:
            st.warning("No properties found for this collection")
            return {}
        
        # Create input fields based on property types
        for prop in properties:
            prop_name = prop['name']
            prop_type = prop['data_type']
            prop_description = prop.get('description', '')
            
            # Create label with description if available
            label = prop_name.title().replace('_', ' ')
            if prop_description:
                label += f" ({prop_description})"
            
            # Handle different data types
            if prop_type == DataType.TEXT:
                if prop_name.lower() in ['description', 'content', 'body', 'summary']:
                    # Use text area for longer text fields
                    value = st.text_area(
                        label,
                        placeholder=f"Enter {prop_name}",
                        height=100,
                        key=f"prop_{prop_name}"
                    )
                else:
                    # Use text input for shorter text fields
                    value = st.text_input(
                        label,
                        placeholder=f"Enter {prop_name}",
                        key=f"prop_{prop_name}"
                    )
                document_data[prop_name] = value.strip() if value else ""
                
            elif prop_type == DataType.INT:
                value = st.number_input(
                    label,
                    value=0,
                    step=1,
                    key=f"prop_{prop_name}"
                )
                document_data[prop_name] = int(value)
                
            elif prop_type == DataType.NUMBER:
                value = st.number_input(
                    label,
                    value=0.0,
                    step=0.1,
                    key=f"prop_{prop_name}"
                )
                document_data[prop_name] = float(value)
                
            elif prop_type == DataType.BOOL:
                value = st.checkbox(
                    label,
                    key=f"prop_{prop_name}"
                )
                document_data[prop_name] = value
                
            elif prop_type == DataType.BLOB:
                # Handle blob data (typically images for multi2vec-clip)
                if vectorizer == 'multi2vec_clip' and prop_name.lower() == 'image':
                    st.markdown(f"**{label}**")
                    uploaded_file = st.file_uploader(
                        "Upload Image",
                        type=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
                        key=f"prop_{prop_name}",
                        help="Upload an image file for multimodal embedding"
                    )
                    if uploaded_file:
                        # Convert to base64
                        image_bytes = uploaded_file.getvalue()
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        document_data[prop_name] = image_base64
                        st.success(f"Image uploaded: {uploaded_file.name}")
                    else:
                        document_data[prop_name] = ""
                else:
                    # Generic blob handling
                    uploaded_file = st.file_uploader(
                        f"Upload file for {label}",
                        key=f"prop_{prop_name}"
                    )
                    if uploaded_file:
                        file_bytes = uploaded_file.getvalue()
                        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                        document_data[prop_name] = file_base64
                        st.success(f"File uploaded: {uploaded_file.name}")
                    else:
                        document_data[prop_name] = ""
                        
            elif prop_type == DataType.DATE:
                value = st.date_input(
                    label,
                    key=f"prop_{prop_name}"
                )
                document_data[prop_name] = value.isoformat() if value else ""
                
            else:
                # Fallback for other types
                value = st.text_input(
                    f"{label} (Type: {prop_type})",
                    placeholder=f"Enter {prop_name}",
                    key=f"prop_{prop_name}"
                )
                document_data[prop_name] = value.strip() if value else ""
        
        # Submit button
        submit_button = st.form_submit_button(
            "Add Document",
            use_container_width=True,
            type="primary"
        )
        
        return document_data if submit_button else None

# Handle document submission
def handle_document_submission(client, collection_name: str, document_data: Dict[str, Any]):
    """Handle the submission of a new document"""
    try:
        # Validate required fields
        if not any(str(value).strip() for value in document_data.values() if value is not None):
            st.error("Please fill in at least one field")
            return
        
        # Remove empty fields
        cleaned_data = {k: v for k, v in document_data.items() 
                       if v is not None and str(v).strip() != ""}
        
        if not cleaned_data:
            st.error("No valid data to submit")
            return
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        progress_messages = []
        
        # Upload the document
        success_count = 0
        error_count = 0
        
        for success, message, _ in batch_upload(client, collection_name, [cleaned_data]):
            progress_messages.append(message)
            if success:
                success_count += 1
            else:
                error_count += 1
            
            # Update progress display
            html_content = f"""
            <div style="
                height: 200px;
                overflow-y: auto;
                border: 1px solid #ccc;
                padding: 10px;
                background-color: #f9f9f9;
            ">
            {"<br>".join(progress_messages)}
            </div>
            """
            progress_placeholder.markdown(html_content, unsafe_allow_html=True)
        
        # Show final result
        if success_count > 0:
            st.success(f"✅ Document added successfully to collection '{collection_name}'!")
            
            # Show added data
            with st.expander("View Added Document Data", expanded=False):
                st.json(cleaned_data)
                
            # Clear form data
            for key in st.session_state.keys():
                if key.startswith('prop_'):
                    del st.session_state[key]
            st.rerun()
        else:
            st.error("❌ Failed to add document. Check the progress messages above for details.")
            
    except Exception as e:
        st.error(f"Error adding document: {str(e)}")

# Main page function
def main():
    set_custom_page_config(page_title="Add Document")
    navigate()
    update_side_bar_labels()
    
    # Check if client is connected
    if not st.session_state.get("client_ready"):
        st.warning("⚠️ Please connect to Weaviate first!")
        return
    
    client = st.session_state.client
    initialize_session_state()
    
    st.title("📄 Add New Document")
    st.markdown("Add a new document to an existing collection with multi2vec-clip embedding support.")
    
    # Step 1: Collection Selection
    st.header("1️⃣ Select Collection")
    
    try:
        # Get list of collections
        collections = list_all_collections(client)
        if not collections:
            st.warning("No collections found. Please create a collection first.")
            return
        
        # Convert to list if needed
        if not isinstance(collections, list):
            collections = list(collections.keys())
        
        collections.sort()
        
        # Collection selection
        selected_collection = st.selectbox(
            "Choose a collection to add documents to:",
            options=collections,
            index=None,
            placeholder="Select a collection...",
            help="Choose the collection where you want to add the new document"
        )
        
        if not selected_collection:
            st.info("👆 Please select a collection to continue")
            return
        
        # Step 2: Load Collection Schema
        if selected_collection != st.session_state.selected_collection:
            st.session_state.selected_collection = selected_collection
            st.session_state.collection_schema = get_collection_schema(client, selected_collection)
        
        if not st.session_state.collection_schema:
            st.error(f"Could not load schema for collection '{selected_collection}'")
            return
        
        # Step 3: Dynamic Form
        st.header("2️⃣ Document Details")
        
        document_data = create_dynamic_form(st.session_state.collection_schema)
        
        # Step 4: Handle Submission
        if document_data is not None:
            handle_document_submission(client, selected_collection, document_data)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()