import streamlit as st
import json
from utils.collections.create import (
    get_collection_info,
    get_available_data_types
)
from utils.collections.update_collection_config import get_collection_config
from utils.cluster.collection import list_collections
from utils.page_config import set_custom_page_config
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels

def initialize_session_state():
    """Initialize session state variables"""
    if 'selected_collection_for_edit' not in st.session_state:
        st.session_state.selected_collection_for_edit = None
    if 'collection_config' not in st.session_state:
        st.session_state.collection_config = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

def display_collection_selector():
    """Display collection selector dropdown"""
    st.subheader("✏️ Edit Collection")
    
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
        "Select Collection to Edit",
        options=["Select a collection..."] + sorted(collections),
        key="edit_collection_selector"
    )
    
    if selected_collection != "Select a collection...":
        return selected_collection
    
    return None

def display_collection_info(collection_info):
    """Display current collection information"""
    st.subheader("📋 Current Collection Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Collection Name", collection_info["name"])
    
    with col2:
        st.metric("Object Count", collection_info["object_count"])
    
    with col3:
        vectorizer = collection_info.get("vectorizer", "Unknown")
        st.metric("Vectorizer", vectorizer)

def display_property_editor(collection_info):
    """Display property editor interface"""
    st.subheader("🔧 Edit Properties")
    
    # Warning about property editing limitations
    st.warning(
        "⚠️ **Important**: Weaviate has limitations on property modifications. "
        "You can add new properties but cannot modify or delete existing ones. "
        "Some changes may require recreating the collection.",
        icon="⚠️"
    )
    
    # Display existing properties
    if collection_info.get("properties"):
        st.markdown("**📋 Existing Properties (Read-only)**")
        
        for i, prop in enumerate(collection_info["properties"]):
            with st.expander(f"Property: {prop.get('name', 'Unknown')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input(
                        "Property Name",
                        value=prop.get("name", "N/A"),
                        disabled=True,
                        key=f"existing_prop_name_{i}"
                    )
                    
                    data_type = prop.get("dataType", ["N/A"])[0] if prop.get("dataType") else "N/A"
                    st.text_input(
                        "Data Type",
                        value=data_type,
                        disabled=True,
                        key=f"existing_prop_type_{i}"
                    )
                
                with col2:
                    st.text_area(
                        "Description",
                        value=prop.get("description", "No description"),
                        disabled=True,
                        key=f"existing_prop_desc_{i}",
                        height=100
                    )
                    
                    tokenization = prop.get("tokenization", "N/A")
                    st.text_input(
                        "Tokenization",
                        value=tokenization,
                        disabled=True,
                        key=f"existing_prop_token_{i}"
                    )
    
    # Add new properties section
    st.divider()
    st.subheader("➕ Add New Properties")
    
    # Initialize new properties in session state
    if 'new_properties' not in st.session_state:
        st.session_state.new_properties = []
    
    # Add new property form
    with st.expander("Add New Property", expanded=len(st.session_state.new_properties) == 0):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_prop_name = st.text_input(
                "Property Name",
                placeholder="e.g., category, rating, tags",
                key="new_property_name"
            )
        
        with col2:
            new_prop_type = st.selectbox(
                "Data Type",
                options=get_available_data_types(),
                key="new_property_type"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add Property", type="primary", use_container_width=True):
                if new_prop_name.strip():
                    # Check for duplicates
                    existing_names = [prop['name'].lower() for prop in collection_info.get("properties", [])]
                    new_names = [prop['name'].lower() for prop in st.session_state.new_properties]
                    
                    if new_prop_name.lower() not in existing_names and new_prop_name.lower() not in new_names:
                        st.session_state.new_properties.append({
                            'name': new_prop_name.strip(),
                            'type': new_prop_type,
                            'description': ''
                        })
                        st.success(f"Added new property: {new_prop_name.strip()}")
                        st.rerun()
                    else:
                        st.error("Property name already exists!")
                else:
                    st.error("Please enter a property name")
        
        # Description for new property
        new_prop_description = st.text_area(
            "Property Description (Optional)",
            placeholder="Describe what this property represents",
            key="new_property_description"
        )
    
    # Display new properties to be added
    if st.session_state.new_properties:
        st.markdown("**🆕 New Properties to Add:**")
        
        for i, prop in enumerate(st.session_state.new_properties):
            col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
            
            with col1:
                st.text_input(
                    f"Name {i+1}",
                    value=prop['name'],
                    disabled=True,
                    key=f"new_prop_display_name_{i}"
                )
            
            with col2:
                st.text_input(
                    f"Type {i+1}",
                    value=prop['type'],
                    disabled=True,
                    key=f"new_prop_display_type_{i}"
                )
            
            with col3:
                updated_desc = st.text_input(
                    f"Description {i+1}",
                    value=prop.get('description', ''),
                    placeholder="Optional description",
                    key=f"new_prop_edit_desc_{i}"
                )
                # Update description in session state
                st.session_state.new_properties[i]['description'] = updated_desc
            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete_new_prop_{i}", help="Remove this property"):
                    st.session_state.new_properties.pop(i)
                    st.rerun()
        
        # Action buttons for new properties
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All New Properties", type="secondary", use_container_width=True):
                st.session_state.new_properties = []
                st.rerun()
        
        with col2:
            if st.button("💾 Apply New Properties", type="primary", use_container_width=True):
                apply_new_properties(collection_info["name"])

def apply_new_properties(collection_name):
    """Apply new properties to the collection"""
    if not st.session_state.new_properties:
        st.warning("No new properties to apply.")
        return
    
    st.warning(
        "⚠️ **Note**: Adding properties to existing collections is not directly supported by Weaviate. "
        "This would typically require recreating the collection with the new schema and migrating data. "
        "Consider using the Weaviate API or client libraries for advanced schema modifications."
    )
    
    # Display what would be applied
    st.subheader("📋 Properties to Apply")
    for prop in st.session_state.new_properties:
        st.markdown(f"• **{prop['name']}** ({prop['type']})" + (f" - {prop['description']}" if prop.get('description') else ""))
    
    # For now, just show the JSON that would be used
    with st.expander("🔧 Property Schema (JSON)", expanded=False):
        properties_json = json.dumps(st.session_state.new_properties, indent=2)
        st.code(properties_json, language="json")
        
        st.info(
            "💡 **Tip**: You can use this JSON schema with Weaviate client libraries or API "
            "to programmatically add these properties to your collection."
        )

def display_collection_config(collection_name):
    """Display and allow editing of collection configuration"""
    st.subheader("⚙️ Collection Configuration")
    
    try:
        config = get_collection_config(st.session_state.client, collection_name)
        
        if config:
            st.markdown("**Current Configuration:**")
            
            # Display configuration in an expandable JSON viewer
            with st.expander("📄 View Full Configuration", expanded=False):
                st.json(config)
            
            # Display key configuration items
            col1, col2 = st.columns(2)
            
            with col1:
                if 'vectorizer' in config:
                    st.metric("Vectorizer", config['vectorizer'])
                
                if 'replicationConfig' in config:
                    replication = config['replicationConfig']
                    st.metric("Replication Factor", replication.get('factor', 'N/A'))
            
            with col2:
                if 'shardingConfig' in config:
                    sharding = config['shardingConfig']
                    st.metric("Virtual Per Physical", sharding.get('virtualPerPhysical', 'N/A'))
                
                if 'invertedIndexConfig' in config:
                    inverted = config['invertedIndexConfig']
                    st.metric("Cleanup Interval", inverted.get('cleanupIntervalSeconds', 'N/A'))
            
            st.info(
                "ℹ️ **Note**: Most collection configuration settings cannot be modified after creation. "
                "For significant changes, consider creating a new collection with the desired configuration."
            )
        
        else:
            st.warning("Could not retrieve collection configuration.")
    
    except Exception as e:
        st.error(f"Error retrieving collection configuration: {str(e)}")

def main():
    """Main function"""
    set_custom_page_config(page_title="Edit Collections")
    navigate()
    
    if st.session_state.get("client_ready"):
        update_side_bar_labels()
        initialize_session_state()
        
        st.title("✏️ Edit Collections")
        st.markdown("Modify collection properties and view configuration details.")
        
        # Collection selector
        selected_collection = display_collection_selector()
        
        if selected_collection:
            st.session_state.selected_collection_for_edit = selected_collection
            
            # Load collection details
            with st.spinner(f"Loading details for '{selected_collection}'..."):
                success, message, collection_info = get_collection_info(
                    st.session_state.client, 
                    selected_collection
                )
                
                if success and collection_info:
                    # Display current collection info
                    display_collection_info(collection_info)
                    
                    st.divider()
                    
                    # Tabs for different editing options
                    tab1, tab2 = st.tabs(["📋 Properties", "⚙️ Configuration"])
                    
                    with tab1:
                        display_property_editor(collection_info)
                    
                    with tab2:
                        display_collection_config(selected_collection)
                
                else:
                    st.error(f"Failed to load collection details: {message}")
        
        # Help section
        with st.expander("ℹ️ Help", expanded=False):
            st.markdown("""
            **How to use Edit Collections:**
            
            1. **Select Collection**: Choose a collection from the dropdown
            2. **View Current State**: See existing properties and configuration
            3. **Add Properties**: Define new properties to add to the collection
            4. **Review Configuration**: View current collection settings
            
            **Important Limitations:**
            - Existing properties cannot be modified or deleted
            - Most configuration settings cannot be changed after creation
            - Adding properties may require advanced API usage
            - Consider creating a new collection for major schema changes
            
            **Recommendations:**
            - Test schema changes in a development environment first
            - Backup your data before making significant changes
            - Use Weaviate client libraries for complex modifications
            """)
    
    else:
        st.warning("Please establish a connection to Weaviate in the Cluster page!")

if __name__ == "__main__":
    main()