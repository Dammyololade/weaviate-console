import streamlit as st

# Update the side bar labels on the fly
def update_side_bar_labels():
    print("update_side_bar_labels called")
    if not st.session_state.get("client_ready"):
        st.warning("Please Establish a connection to Weaviate on the side bar")
    # Connection status is now displayed in the info dialog instead of cluttering the sidebar

# Clear the session state
def clear_session_state():
    print("clear_session_state called")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()
    st.rerun()
