import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from utils.connection.weaviate_connection import get_weaviate_client
from utils.page_config import set_custom_page_config
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels
from utils.collections.create import create_collection_with_properties
from weaviate.classes.config import Property, DataType, Configure

# Backup history collection name
BACKUP_HISTORY_COLLECTION = "BackupHistory"

def initialize_backup_history_collection(client):
    """Initialize the backup history collection if it doesn't exist"""
    try:
        if not client.collections.exists(BACKUP_HISTORY_COLLECTION):
            # Define properties for backup metadata
            backup_properties = [
                {"name": "backup_id", "type": "TEXT", "description": "Unique backup identifier"},
                {"name": "provider", "type": "TEXT", "description": "Backup provider (filesystem, s3, gcs, azure)"},
                {"name": "status", "type": "TEXT", "description": "Backup status (SUCCESS, FAILED, IN_PROGRESS)"},
                {"name": "created_date", "type": "DATE", "description": "Backup creation timestamp"},
                {"name": "collections", "type": "TEXT_ARRAY", "description": "List of collections included in backup"},
                {"name": "path", "type": "TEXT", "description": "Backup storage path"},
                {"name": "size_bytes", "type": "INT", "description": "Backup size in bytes"},
                {"name": "error_message", "type": "TEXT", "description": "Error message if backup failed"},
                {"name": "completion_time", "type": "DATE", "description": "Backup completion timestamp"}
            ]
            
            success, message = create_collection_with_properties(
                client, 
                BACKUP_HISTORY_COLLECTION, 
                "BYOV",  # No vectorization needed for metadata
                backup_properties
            )
            
            if success:
                st.success(f"✅ Backup history collection initialized: {message}")
            else:
                st.error(f"❌ Failed to initialize backup history collection: {message}")
                
    except Exception as e:
        st.error(f"❌ Error initializing backup history collection: {str(e)}")

def store_backup_metadata(client, backup_id: str, provider: str, collections: List[str], 
                         status: str = "IN_PROGRESS", path: str = "", size_bytes: int = 0, 
                         error_message: str = "", completion_time: datetime = None):
    """Store backup metadata in the backup history collection"""
    try:
        if not client.collections.exists(BACKUP_HISTORY_COLLECTION):
            initialize_backup_history_collection(client)
        
        collection = client.collections.get(BACKUP_HISTORY_COLLECTION)
        
        metadata = {
            "backup_id": backup_id,
            "provider": provider,
            "status": status,
            "created_date": datetime.now(),
            "collections": collections,
            "path": path,
            "size_bytes": size_bytes,
            "error_message": error_message,
            "completion_time": completion_time or datetime.now() if status in ["SUCCESS", "FAILED"] else None
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        collection.data.insert(metadata)
        return True, "Backup metadata stored successfully"
        
    except Exception as e:
        return False, f"Error storing backup metadata: {str(e)}"

def get_backup_history(client, limit: int = 100):
    """Retrieve backup history from the collection"""
    try:
        if not client.collections.exists(BACKUP_HISTORY_COLLECTION):
            return []
        
        collection = client.collections.get(BACKUP_HISTORY_COLLECTION)
        
        # Use fetch_objects instead of iterator with limit
        response = collection.query.fetch_objects(limit=limit)
        backups = []
        
        for item in response.objects:
            backup_data = item.properties
            backup_data['uuid'] = str(item.uuid)
            backups.append(backup_data)
        
        # Sort by created_date descending (newest first)
        backups.sort(key=lambda x: x.get('created_date', datetime.min), reverse=True)
        return backups
        
    except Exception as e:
        st.error(f"Error retrieving backup history: {str(e)}")
        return []

def update_backup_status(client, backup_id: str, status: str, error_message: str = "", 
                        size_bytes: int = 0, path: str = ""):
    """Update backup status in the history collection"""
    try:
        if not client.collections.exists(BACKUP_HISTORY_COLLECTION):
            return False, "Backup history collection not found"
        
        collection = client.collections.get(BACKUP_HISTORY_COLLECTION)
        
        # Find the backup record using simple fetch_objects
        response = collection.query.fetch_objects(limit=1000)
        
        # Filter manually for the backup_id
        matching_objects = []
        for obj in response.objects:
            if obj.properties.get("backup_id") == backup_id:
                matching_objects.append(obj)
                break
        
        if matching_objects:
            backup_uuid = matching_objects[0].uuid
            
            # Update the record
            update_data = {
                "status": status,
                "completion_time": datetime.now()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            if size_bytes > 0:
                update_data["size_bytes"] = size_bytes
            if path:
                update_data["path"] = path
                
            collection.data.update(
                uuid=backup_uuid,
                properties=update_data
            )
            
            return True, "Backup status updated successfully"
        else:
            return False, f"Backup record not found for ID: {backup_id}"
            
    except Exception as e:
        return False, f"Error updating backup status: {str(e)}"

def delete_backup_record(client, backup_uuid: str):
    """Delete a backup record from the history collection"""
    try:
        if not client.collections.exists(BACKUP_HISTORY_COLLECTION):
            return False, "Backup history collection not found"
        
        collection = client.collections.get(BACKUP_HISTORY_COLLECTION)
        collection.data.delete_by_id(backup_uuid)
        
        return True, "Backup record deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting backup record: {str(e)}"

# Initialize session state for backup operations
def initialize_backup_session_state():
    """Initialize session state variables for backup management"""
    if "backup_operations" not in st.session_state:
        st.session_state.backup_operations = {}
    if "backup_provider" not in st.session_state:
        st.session_state.backup_provider = "filesystem"
    if "backup_list" not in st.session_state:
        st.session_state.backup_list = []
    if "selected_collections" not in st.session_state:
        st.session_state.selected_collections = []

# Backup provider selection
def backup_provider_selection():
    """Select backup storage provider (configured via environment variables)"""
    st.subheader("🗄️ Storage Provider Selection")
    
    provider = st.selectbox(
        "Select Backup Provider",
        options=["filesystem", "s3", "gcs", "azure"],
        index=["filesystem", "s3", "gcs", "azure"].index(st.session_state.backup_provider),
        help="Choose your backup storage provider (must be configured in Weaviate deployment)"
    )
    st.session_state.backup_provider = provider
    
    # Display provider information
    if provider == "filesystem":
        st.info("📁 **Filesystem Storage**: Suitable for development and testing. Not recommended for production.")
        st.markdown("**Configuration**: Set `BACKUP_FILESYSTEM_PATH` environment variable in your Weaviate deployment.")
    elif provider == "s3":
        st.info("☁️ **AWS S3 Storage**: Recommended for production deployments. Supports multi-node setups.")
        st.markdown("**Configuration**: Set `BACKUP_S3_BUCKET`, `BACKUP_S3_PATH`, and authentication environment variables in your Weaviate deployment.")
    elif provider == "gcs":
        st.info("🌐 **Google Cloud Storage**: Recommended for production on GCP. Supports multi-node setups.")
        st.markdown("**Configuration**: Set `BACKUP_GCS_BUCKET`, `BACKUP_GCS_PATH`, and authentication environment variables in your Weaviate deployment.")
    elif provider == "azure":
        st.info("🔷 **Azure Storage**: Recommended for production on Azure. Supports multi-node setups.")
        st.markdown("**Configuration**: Set `BACKUP_AZURE_CONTAINER`, `BACKUP_AZURE_PATH`, and authentication environment variables in your Weaviate deployment.")
    
    return {"provider": provider}

def get_collections_list(client):
    """Get list of available collections"""
    try:
        collections = client.collections.list_all()
        return list(collections.keys()) if collections else []
    except Exception as e:
        st.error(f"Error fetching collections: {str(e)}")
        return []

def create_backup_form(client, storage_config):
    """Form for creating a new backup"""
    st.subheader("📦 Create Backup")
    
    with st.form("create_backup_form"):
        # Backup ID
        backup_id = st.text_input(
            "Backup ID",
            value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Unique identifier for this backup"
        )
        
        # Collection selection
        collections = get_collections_list(client)
        if collections:
            include_all = st.checkbox("Include All Collections", value=True)
            
            if not include_all:
                selected_collections = st.multiselect(
                    "Select Collections to Backup",
                    options=collections,
                    default=st.session_state.selected_collections,
                    help="Choose specific collections to include in the backup"
                )
                st.session_state.selected_collections = selected_collections
            else:
                selected_collections = collections
        else:
            st.warning("No collections found in the database.")
            selected_collections = []
        
        # Advanced options
        with st.expander("⚙️ Advanced Options", expanded=False):
            wait_for_completion = st.checkbox(
                "Wait for Completion",
                value=True,
                help="Wait for backup to complete before returning"
            )
            
            compression = st.selectbox(
                "Compression",
                options=["gzip", "none"],
                help="Compression method for backup files"
            )
        
        # Submit button
        if st.form_submit_button("🚀 Start Backup", type="primary"):
            if backup_id and selected_collections:
                create_backup(client, backup_id, storage_config["provider"], selected_collections, wait_for_completion)
            else:
                st.error("Please provide a backup ID and select at least one collection.")

def create_backup(client, backup_id: str, provider: str, collections: List[str], wait_for_completion: bool = True):
    """Execute backup creation"""
    try:
        # Initialize session state for backup operations if not exists
        if 'backup_operations' not in st.session_state:
            st.session_state.backup_operations = {}
        
        # Store initial backup metadata with IN_PROGRESS status
        metadata_success, metadata_msg = store_backup_metadata(client, backup_id, provider, collections, "IN_PROGRESS")
        if not metadata_success:
            st.warning(f"⚠️ Could not store backup metadata: {metadata_msg}")
            st.info("Backup will proceed, but history tracking may be incomplete.")
        
        with st.spinner(f"Creating backup '{backup_id}'..."):
            # Create backup using the configured provider
            # Note: Storage configuration (paths, credentials, etc.) must be set via environment variables
            result = client.backup.create(
                backup_id=backup_id,
                backend=provider,
                include_collections=collections,
                wait_for_completion=wait_for_completion
            )
            
            # Update backup status to SUCCESS
            status_success, status_msg = update_backup_status(client, backup_id, "SUCCESS")
            if not status_success:
                st.warning(f"⚠️ Could not update backup status: {status_msg}")
            
            # Store operation in session state
            st.session_state.backup_operations[backup_id] = {
                "type": "create",
                "status": "completed" if wait_for_completion else "in_progress",
                "collections": collections,
                "created_at": datetime.now().isoformat(),
                "provider": provider
            }
            
            if wait_for_completion:
                st.success(f"✅ Backup '{backup_id}' created successfully!")
                if metadata_success:
                    st.info("📝 Backup metadata has been logged to history.")
                st.json(result)
            else:
                st.info(f"🔄 Backup '{backup_id}' started. Check progress below.")
                
    except Exception as e:
        error_msg = str(e)
        # Update backup status to FAILED with error message
        status_success, status_msg = update_backup_status(client, backup_id, "FAILED", error_msg)
        if not status_success:
            st.warning(f"⚠️ Could not update backup status: {status_msg}")
        st.error(f"❌ Backup creation failed: {error_msg}")

def restore_backup_form(client, storage_config):
    """Form for restoring a backup"""
    st.subheader("🔄 Restore Backup")
    
    with st.form("restore_backup_form"):
        # Backup ID to restore
        backup_id = st.text_input(
            "Backup ID to Restore",
            help="Enter the ID of the backup you want to restore"
        )
        
        # Advanced options
        with st.expander("⚙️ Restore Options", expanded=False):
            include_collections = st.text_area(
                "Include Collections (Optional)",
                placeholder="Leave empty to restore all collections\nOr enter collection names, one per line",
                help="Specify which collections to restore. Leave empty to restore all."
            )
            
            exclude_collections = st.text_area(
                "Exclude Collections (Optional)",
                placeholder="Enter collection names to exclude, one per line",
                help="Specify which collections to exclude from restore."
            )
            
            wait_for_completion = st.checkbox(
                "Wait for Completion",
                value=True,
                help="Wait for restore to complete before returning"
            )
        
        # Submit button
        if st.form_submit_button("🔄 Start Restore", type="primary"):
            if backup_id:
                # Parse collection lists
                include_list = [c.strip() for c in include_collections.split('\n') if c.strip()] if include_collections else None
                exclude_list = [c.strip() for c in exclude_collections.split('\n') if c.strip()] if exclude_collections else None
                
                restore_backup(client, backup_id, storage_config["provider"], include_list, exclude_list, wait_for_completion)
            else:
                st.error("Please provide a backup ID to restore.")

def restore_backup(client, backup_id: str, provider: str, include_collections: Optional[List[str]] = None, exclude_collections: Optional[List[str]] = None, wait_for_completion: bool = True):
    """Execute backup restoration"""
    try:
        with st.spinner(f"Restoring backup '{backup_id}'..."):
            # Restore backup using the configured provider
            # Note: Storage configuration (paths, credentials, etc.) must be set via environment variables
            result = client.backup.restore(
                backup_id=backup_id,
                backend=provider,
                include_collections=include_collections,
                exclude_collections=exclude_collections,
                wait_for_completion=wait_for_completion
            )
            
            # Store operation in session state
            st.session_state.backup_operations[f"restore_{backup_id}"] = {
                "type": "restore",
                "backup_id": backup_id,
                "status": "completed" if wait_for_completion else "in_progress",
                "include_collections": include_collections,
                "exclude_collections": exclude_collections,
                "started_at": datetime.now().isoformat(),
                "provider": provider
            }
            
            if wait_for_completion:
                st.success(f"✅ Backup '{backup_id}' restored successfully!")
                st.json(result)
            else:
                st.info(f"🔄 Restore of '{backup_id}' started. Check progress below.")
                
    except Exception as e:
        st.error(f"❌ Backup restoration failed: {str(e)}")

def check_backup_status(client, backup_id: str, backend: str):
    """Check the status of a backup operation"""
    try:
        status = client.backup.get_restore_status(backup_id=backup_id, backend=backend)
        return status
    except Exception as e:
        st.error(f"Error checking backup status: {str(e)}")
        return None

def backup_operations_monitor():
    """Monitor ongoing backup operations"""
    st.subheader("📊 Backup Operations Monitor")
    
    # Initialize backup operations if not exists
    if 'backup_operations' not in st.session_state:
        st.session_state.backup_operations = {}
    
    if not st.session_state.backup_operations:
        st.info("No backup operations to monitor.")
        return
    
    # Refresh button
    if st.button("🔄 Refresh Status", type="secondary"):
        st.rerun()
    
    # Display operations
    for op_id, operation in st.session_state.backup_operations.items():
        with st.expander(f"{operation['type'].title()}: {op_id}", expanded=operation['status'] == 'in_progress'):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Type", operation['type'].title())
                st.metric("Status", operation['status'].title())
            
            with col2:
                if operation['type'] == 'create':
                    st.metric("Collections", len(operation.get('collections', [])))
                    st.metric("Created", operation.get('created_at', 'Unknown')[:19])
                else:
                    st.metric("Backup ID", operation.get('backup_id', 'Unknown'))
                    st.metric("Started", operation.get('started_at', 'Unknown')[:19])
            
            with col3:
                st.metric("Provider", operation.get('provider', 'Unknown'))
                
                # Action buttons
                if operation['status'] == 'in_progress':
                    if st.button(f"❌ Cancel {op_id}", key=f"cancel_{op_id}"):
                        # Implement cancellation logic here
                        st.warning("Cancellation requested (implementation needed)")
            
            # Show collections if available
            if operation.get('collections'):
                st.markdown("**Collections:**")
                st.write(", ".join(operation['collections']))

def backup_management(client):
    """Backup history management with restore and delete functionality"""
    st.subheader("🗂️ Backup History & Management")
    
    # Initialize backup history collection
    initialize_backup_history_collection(client)
    
    # Debug: Show collection status
    with st.expander("🔍 Debug Information", expanded=False):
        try:
            collection_exists = client.collections.exists(BACKUP_HISTORY_COLLECTION)
            st.write(f"**Collection '{BACKUP_HISTORY_COLLECTION}' exists:** {collection_exists}")
            
            if collection_exists:
                collection = client.collections.get(BACKUP_HISTORY_COLLECTION)
                # Try to get a count of objects
                try:
                    response = collection.query.fetch_objects(limit=1)
                    st.write(f"**Collection accessible:** ✅ Yes")
                    st.write(f"**Sample query successful:** ✅ Yes")
                except Exception as e:
                    st.write(f"**Collection accessible:** ❌ No - {str(e)}")
            else:
                st.write("**Collection needs to be created**")
        except Exception as e:
            st.write(f"**Debug error:** {str(e)}")
    
    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", help="Refresh backup history"):
            st.rerun()
    
    # Get backup history
    backup_history = get_backup_history(client)
    
    if backup_history:
        st.markdown(f"**Found {len(backup_history)} backup(s) in history:**")
        
        for backup in backup_history:
            with st.container():
                # Create columns for backup information
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1.5, 1])
                
                with col1:
                    # Status indicator
                    status = backup.get('status', 'UNKNOWN')
                    status_icon = {
                        'SUCCESS': '✅',
                        'FAILED': '❌', 
                        'IN_PROGRESS': '🔄'
                    }.get(status, '❓')
                    
                    st.write(f"{status_icon} **{backup.get('backup_id', 'Unknown')}**")
                    
                    # Show creation date
                    created_date = backup.get('created_date')
                    if created_date:
                        if isinstance(created_date, str):
                            st.caption(f"Created: {created_date}")
                        else:
                            st.caption(f"Created: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.write(f"**Provider:** {backup.get('provider', 'Unknown')}")
                    collections = backup.get('collections', [])
                    if collections:
                        st.caption(f"Collections: {', '.join(collections[:3])}{'...' if len(collections) > 3 else ''}")
                
                with col3:
                    st.write(f"**Status:** {status}")
                    if backup.get('error_message'):
                        st.caption(f"❌ {backup['error_message'][:50]}...")
                    
                    # Show size if available
                    size_bytes = backup.get('size_bytes', 0)
                    if size_bytes > 0:
                        size_mb = size_bytes / (1024 * 1024)
                        st.caption(f"Size: {size_mb:.1f} MB")
                
                with col4:
                    # Restore button (only for successful backups)
                    if status == 'SUCCESS':
                        if st.button(f"🔄 Restore", key=f"restore_{backup['uuid']}", help="Restore this backup"):
                            backup_id = backup.get('backup_id')
                            provider = backup.get('provider')
                            
                            if backup_id and provider:
                                with st.spinner(f"Restoring backup '{backup_id}'..."):
                                    try:
                                        result = client.backup.restore(
                                            backup_id=backup_id,
                                            backend=provider
                                        )
                                        
                                        if result:
                                            st.success(f"✅ Backup '{backup_id}' restoration started!")
                                            # Store operation in session state
                                            operation = {
                                                "id": f"restore_{backup_id}",
                                                "type": "restore",
                                                "status": "IN_PROGRESS",
                                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                "backup_id": backup_id,
                                                "provider": provider
                                            }
                                            st.session_state.backup_operations.append(operation)
                                        else:
                                            st.error(f"❌ Failed to start restoration of backup '{backup_id}'")
                                    except Exception as e:
                                        st.error(f"❌ Error restoring backup: {str(e)}")
                    else:
                        st.write("—")
                
                with col5:
                    # Delete button
                    if st.button(f"🗑️", key=f"delete_{backup['uuid']}", help="Delete this backup record"):
                        success, message = delete_backup_record(client, backup['uuid'])
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                
                # Show additional details in an expander
                with st.expander(f"📋 Details for {backup.get('backup_id', 'Unknown')}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Backup ID:** {backup.get('backup_id', 'N/A')}")
                        st.write(f"**Provider:** {backup.get('provider', 'N/A')}")
                        st.write(f"**Status:** {backup.get('status', 'N/A')}")
                        st.write(f"**Path:** {backup.get('path', 'N/A')}")
                    
                    with col_b:
                        created = backup.get('created_date')
                        completed = backup.get('completion_time')
                        
                        if created:
                            if isinstance(created, str):
                                st.write(f"**Created:** {created}")
                            else:
                                st.write(f"**Created:** {created.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if completed:
                            if isinstance(completed, str):
                                st.write(f"**Completed:** {completed}")
                            else:
                                st.write(f"**Completed:** {completed.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        collections = backup.get('collections', [])
                        if collections:
                            st.write(f"**Collections ({len(collections)}):** {', '.join(collections)}")
                        
                        if backup.get('error_message'):
                            st.write(f"**Error:** {backup['error_message']}")
                
                st.divider()
    else:
        st.info("📝 No backup history found. Create your first backup to see it here!")
        
        # Option to manually add a backup record
        with st.expander("➕ Manually Add Backup Record"):
            with st.form("manual_backup_form"):
                st.markdown("**Add existing backup to history:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    manual_backup_id = st.text_input("Backup ID", help="Enter the existing backup ID")
                    manual_provider = st.selectbox("Provider", ["filesystem", "s3", "gcs", "azure"])
                
                with col2:
                    manual_collections = st.text_area(
                        "Collections (one per line)", 
                        help="Enter collection names, one per line"
                    )
                    manual_path = st.text_input("Backup Path (optional)", help="Storage path of the backup")
                
                if st.form_submit_button("➕ Add to History"):
                    if manual_backup_id:
                        collections_list = [c.strip() for c in manual_collections.split('\n') if c.strip()]
                        
                        success, message = store_backup_metadata(
                            client, 
                            manual_backup_id, 
                            manual_provider, 
                            collections_list, 
                            "SUCCESS",  # Assume existing backups are successful
                            manual_path
                        )
                        
                        if success:
                            st.success(f"✅ Backup '{manual_backup_id}' added to history!")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please enter a backup ID")

def main():
    """Main function for backup management page"""
    set_custom_page_config(page_title="Backup Management")
    navigate()
    
    if st.session_state.get("client_ready"):
        update_side_bar_labels()
    
    st.markdown("Create, restore, and manage Weaviate database backups.")
    
    # Check if client is ready
    if not st.session_state.get("client_ready"):
        st.error("❌ Not connected to Weaviate")
        st.markdown("Please establish a connection first from the sidebar or connections page.")
        return
    
    # Initialize session state
    initialize_backup_session_state()
    
    # Get Weaviate client from session state
    client = st.session_state.client
    
    # Initialize backup history collection on page load
    try:
        initialize_backup_history_collection(client)
    except Exception as e:
        st.error(f"❌ Error initializing backup history: {str(e)}")
    
    # Storage provider configuration
    storage_config = backup_provider_selection()
    
    st.divider()
    
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Create Backup", "🔄 Restore Backup", "📊 Monitor Operations", "🗂️ Backup History"])
    
    with tab1:
        create_backup_form(client, storage_config)
    
    with tab2:
        restore_backup_form(client, storage_config)
    
    with tab3:
        backup_operations_monitor()
    
    with tab4:
        backup_management(client)
    
    # Help section
    with st.expander("ℹ️ Backup Help", expanded=False):
        st.markdown("""
        **Backup Management Help:**
        
        **Storage Providers:**
        - **Filesystem**: Local storage, suitable for development and testing
        - **AWS S3**: Production-ready cloud storage with multi-node support
        - **Google Cloud Storage**: Production-ready for GCP environments
        - **Azure Storage**: Production-ready for Azure environments
        
        **Important Notes:**
        - Backups include only active tenants in multi-tenant collections
        - Ensure your Weaviate instance has the appropriate backup modules enabled
        - For production, always use cloud storage providers (S3, GCS, Azure)
        - Backup IDs must be unique within the same storage backend
        
        **Version Requirements:**
        - Weaviate v1.23.13 or higher is required to prevent data corruption
        - Ensure backup and restore operations use compatible Weaviate versions
        
        **Security:**
        - API keys and credentials are handled securely
        - Use IAM roles when possible instead of access keys
        - Ensure proper access controls on your backup storage
        """)

if __name__ == "__main__":
    main()