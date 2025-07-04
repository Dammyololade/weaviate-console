import streamlit as st
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels
from utils.cluster.collection import list_collections
from utils.collections.create import get_collection_info
from utils.collections.delete import delete_collections
from utils.page_config import set_custom_page_config

def initialize_session_state():
    """Initialize session state variables"""
    if "selected_collections_for_deletion" not in st.session_state:
        st.session_state.selected_collections_for_deletion = set()
    if "collections_list" not in st.session_state:
        st.session_state.collections_list = []
    if "show_confirmation" not in st.session_state:
        st.session_state.show_confirmation = False

def display_collection_selector():
    """Display collection selector with checkboxes"""
    
    # Get list of collections
    collections = list_collections(st.session_state.client)
    
    if isinstance(collections, dict) and "error" in collections:
        st.error(f"Error loading collections: {collections['error']}")
        return
    
    if not collections:
        st.warning("No collections found.")
        return
    
    st.session_state.collections_list = sorted(collections)
    
    # Warning message
    st.error(
        "⚠️ **DANGER ZONE**: This will permanently delete collections and ALL their data. "
        "This action cannot be undone!",
        icon="⚠️"
    )
    
    # Collection selection
    st.markdown("**Select collections to delete:**")
    
    # Group collections by first letter for better organization
    collections_by_letter = {}
    for col in st.session_state.collections_list:
        first_letter = col[0].upper()
        if first_letter not in collections_by_letter:
            collections_by_letter[first_letter] = []
        collections_by_letter[first_letter].append(col)
    
    # Display collections grouped by letter in expanders
    for letter in sorted(collections_by_letter.keys()):
        with st.expander(f"📁 Collections - {letter}", expanded=len(collections_by_letter) <= 3):
            for col in sorted(collections_by_letter[letter]):
                # Get collection info for display
                success, _, info = get_collection_info(st.session_state.client, col)
                object_count = info.get("object_count", 0) if success and info else "Unknown"
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    is_selected = st.checkbox(
                        f"**{col}**",
                        key=f"delete_col_{col}",
                        value=col in st.session_state.selected_collections_for_deletion
                    )
                    
                    if is_selected:
                        st.session_state.selected_collections_for_deletion.add(col)
                    else:
                        st.session_state.selected_collections_for_deletion.discard(col)
                
                with col2:
                    st.caption(f"Objects: {object_count}")
    
    # Selection summary
    if st.session_state.selected_collections_for_deletion:
        st.markdown(f"**Selected for deletion: {len(st.session_state.selected_collections_for_deletion)} collection(s)**")
        
        # Show selected collections
        with st.expander("📋 Review Selected Collections", expanded=True):
            for col in sorted(st.session_state.selected_collections_for_deletion):
                success, _, info = get_collection_info(st.session_state.client, col)
                object_count = info.get("object_count", 0) if success and info else "Unknown"
                vectorizer = info.get("vectorizer", "Unknown") if success and info else "Unknown"
                
                st.markdown(f"• **{col}** - {object_count} objects, Vectorizer: {vectorizer}")
    
    return len(st.session_state.selected_collections_for_deletion) > 0

def display_deletion_confirmation():
    """Display deletion confirmation interface"""
    st.subheader("⚠️ Confirm Deletion")
    
    selected_collections = list(st.session_state.selected_collections_for_deletion)
    
    st.error(
        f"You are about to permanently delete {len(selected_collections)} collection(s) "
        "and ALL their data. This action cannot be undone!"
    )
    
    # Show what will be deleted
    st.markdown("**Collections to be deleted:**")
    total_objects = 0
    
    for col in selected_collections:
        success, _, info = get_collection_info(st.session_state.client, col)
        object_count = info.get("object_count", 0) if success and info else 0
        total_objects += object_count
        
        st.markdown(f"• **{col}** ({object_count} objects)")
    
    st.error(f"**Total objects to be deleted: {total_objects}**")
    
    # Confirmation input
    st.markdown("**Type 'DELETE' to confirm:**")
    confirmation_text = st.text_input(
        "Confirmation",
        placeholder="Type DELETE to confirm",
        key="deletion_confirmation"
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_confirmation = False
            st.session_state.selected_collections_for_deletion.clear()
            st.rerun()
    
    with col2:
        delete_enabled = confirmation_text.strip().upper() == "DELETE"
        if st.button(
            "🗑️ DELETE COLLECTIONS",
            type="primary",
            disabled=not delete_enabled,
            use_container_width=True
        ):
            if delete_enabled:
                perform_deletion(selected_collections)
            else:
                st.error("Please type 'DELETE' to confirm")

def perform_deletion(collections_to_delete):
    """Perform the actual deletion"""
    st.subheader("🔄 Deleting Collections...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_collections = []
    
    for i, collection in enumerate(collections_to_delete):
        status_text.text(f"Deleting {collection}...")
        progress_bar.progress((i + 1) / len(collections_to_delete))
        
        try:
            success, message = delete_collections(st.session_state.client, [collection])
            
            if success:
                success_count += 1
                st.success(f"✅ Deleted: {collection}")
            else:
                failed_collections.append((collection, message))
                st.error(f"❌ Failed to delete {collection}: {message}")
        
        except Exception as e:
            failed_collections.append((collection, str(e)))
            st.error(f"❌ Error deleting {collection}: {str(e)}")
    
    # Final results
    status_text.text("Deletion completed!")
    
    if success_count > 0:
        st.success(f"✅ Successfully deleted {success_count} collection(s)")
    
    if failed_collections:
        st.error(f"❌ Failed to delete {len(failed_collections)} collection(s)")
        with st.expander("View Failed Deletions"):
            for collection, error in failed_collections:
                st.markdown(f"• **{collection}**: {error}")
    
    # Reset state
    st.session_state.show_confirmation = False
    st.session_state.selected_collections_for_deletion.clear()
    
    # Refresh button
    if st.button("🔄 Refresh Page", use_container_width=True):
        st.rerun()

def main():
    """Main function"""
    set_custom_page_config(page_title="Delete Collections")
    navigate()
    
    if st.session_state.get("client_ready"):
        update_side_bar_labels()
        initialize_session_state()
        
        st.markdown("Permanently delete collections and all their data from your Weaviate instance.")
        
        if not st.session_state.show_confirmation:
            # Collection selection phase
            has_selections = display_collection_selector()
            
            if has_selections:
                st.divider()
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🗑️ Delete Selected Collections", type="primary", use_container_width=True):
                        st.session_state.show_confirmation = True
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Clear Selection", use_container_width=True):
                        st.session_state.selected_collections_for_deletion.clear()
                        st.rerun()
        
        else:
            # Confirmation phase
            display_deletion_confirmation()
        
        # Help section
        with st.expander("ℹ️ Help & Safety Information", expanded=False):
            st.markdown("""
            **How to use Delete Collections:**
            
            1. **Select Collections**: Choose collections you want to delete
            2. **Review Selection**: Verify the collections and their object counts
            3. **Confirm Deletion**: Type 'DELETE' to confirm the permanent deletion
            4. **Monitor Progress**: Watch the deletion progress and results
            
            **⚠️ Important Safety Notes:**
            
            - **Permanent Action**: Deleted collections and data cannot be recovered
            - **Admin Privileges**: Ensure you have admin access to the Weaviate instance
            - **Backup First**: Consider backing up important data before deletion
            - **Production Warning**: Be extra careful when working with production data
            - **Dependencies**: Check if other applications depend on these collections
            
            **Best Practices:**
            
            - Test deletions in a development environment first
            - Delete collections during maintenance windows
            - Verify collection names carefully before confirming
            - Keep a record of deleted collections for audit purposes
            """)
    
    else:
        st.warning("Please establish a connection to Weaviate in the Cluster page!")

if __name__ == "__main__":
    main()