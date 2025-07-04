import streamlit as st
import pandas as pd
from utils.collections.create import get_collection_info
from utils.cluster.collection import list_collections
from utils.page_config import set_custom_page_config
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels

def initialize_session_state():
    """Initialize session state variables"""
    if 'selected_collection_for_read' not in st.session_state:
        st.session_state.selected_collection_for_read = None
    if 'collection_details' not in st.session_state:
        st.session_state.collection_details = None

def display_collection_selector():
    """Display collection selector dropdown"""
    
    # Get list of collections
    collections = list_collections(st.session_state.client)
    
    if isinstance(collections, dict) and "error" in collections:
        st.error(f"Error loading collections: {collections['error']}")
        return None
    
    if not collections:
        st.warning("No collections found. Create a collection first.")
        return None
    
    # Collection selector
    selected_collection = st.selectbox(
        "Select Collection to View",
        options=["Select a collection..."] + sorted(collections),
        key="collection_selector"
    )
    
    if selected_collection != "Select a collection...":
        return selected_collection
    
    return None

def display_collection_schema(collection_info):
    """Display collection schema information"""
    st.subheader("🔧 Collection Schema")
    
    # Basic information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Collection Name", collection_info["name"])
    
    with col2:
        st.metric("Object Count", collection_info["object_count"])
    
    with col3:
        vectorizer = collection_info.get("vectorizer", "Unknown")
        st.metric("Vectorizer", vectorizer)
    
    # Properties information
    if collection_info.get("properties"):
        st.subheader("📋 Properties")
        
        # Create a DataFrame for properties
        properties_data = []
        for prop in collection_info["properties"]:
            properties_data.append({
                "Property Name": prop.get("name", "N/A"),
                "Data Type": prop.get("dataType", ["N/A"])[0] if prop.get("dataType") else "N/A",
                "Description": prop.get("description", "No description"),
                "Tokenization": prop.get("tokenization", "N/A")
            })
        
        if properties_data:
            df_properties = pd.DataFrame(properties_data)
            st.dataframe(df_properties, use_container_width=True)
        else:
            st.info("No custom properties defined for this collection.")
    else:
        st.info("No schema information available.")
    
    # Additional configuration details
    if collection_info.get("config"):
        with st.expander("⚙️ Advanced Configuration", expanded=False):
            config = collection_info["config"]
            st.json(config)

def display_collection_summary(collection_info):
    """Display collection summary information"""
    st.subheader("📊 Collection Summary")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Objects", collection_info["object_count"])
    
    with col2:
        property_count = len(collection_info.get("properties", []))
        st.metric("Properties", property_count)
    
    with col3:
        vectorizer = collection_info.get("vectorizer", "Unknown")
        st.metric("Vectorizer", vectorizer)
    
    with col4:
        # Check if multi-tenancy is enabled
        config = collection_info.get("config", {})
        mt_enabled = config.get("multiTenancyConfig", {}).get("enabled", False)
        st.metric("Multi-Tenancy", "Enabled" if mt_enabled else "Disabled")

def main():
    """Main function"""
    set_custom_page_config(page_title="Read Collections")
    navigate()
    
    if st.session_state.get("client_ready"):
        update_side_bar_labels()
        initialize_session_state()
        
        st.markdown("View detailed information about your Weaviate collections, including schema and configuration.")
        
        # Collection selector
        selected_collection = display_collection_selector()
        
        if selected_collection:
            st.session_state.selected_collection_for_read = selected_collection
            
            # Load collection details
            with st.spinner(f"Loading details for '{selected_collection}'..."):
                success, message, collection_info = get_collection_info(
                    st.session_state.client, 
                    selected_collection
                )
                
                if success and collection_info:
                    st.session_state.collection_details = collection_info
                    
                    # Display collection summary
                    display_collection_summary(collection_info)
                    
                    st.divider()
                    
                    # Display collection schema
                    display_collection_schema(collection_info)
                    
                else:
                    st.error(f"Failed to load collection details: {message}")
        
        # Show help information
        with st.expander("ℹ️ Help", expanded=False):
            st.markdown("""
            **How to use Read Collections:**
            
            1. **Select Collection**: Choose a collection from the dropdown to view its details
            2. **View Summary**: See key metrics like object count, properties, and configuration
            3. **View Schema**: Examine the collection's properties, data types, and settings
            4. **Advanced Config**: Expand to see detailed configuration in JSON format
            
            **Note**: This page shows collection metadata only. To view actual data objects, use the Documents section.
            """)
    
    else:
        st.warning("Please establish a connection to Weaviate in the Cluster page!")

if __name__ == "__main__":
    main()