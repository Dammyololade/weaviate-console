import streamlit as st
import time
from utils.connection.weaviate_client import initialize_client
from utils.connection.weaviate_connection import close_weaviate_client
from utils.sidebar.navigation import navigate
from utils.sidebar.helper import update_side_bar_labels, clear_session_state
from utils.page_config import set_custom_page_config

@st.dialog("🔗 Weaviate Connection Configuration")
def show_connection_dialog():
    """Display the connection configuration dialog"""
    # Initialize connection session state before displaying form
    initialize_connection_session_state()
    display_connection_form()

@st.dialog("ℹ️ Connection Information")
def show_connection_info_dialog():
    """Display the connection information dialog"""
    if not st.session_state.get("client_ready"):
        st.error("❌ Not connected to Weaviate")
        st.markdown("Please establish a connection first.")
    else:
        st.success("✅ Connected to Weaviate")
        
        # Connection details in a clean layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📍 Endpoint**")
            st.markdown(f"<div style='font-size: 16px; word-wrap: break-word;'>{st.session_state.get('active_endpoint', 'N/A')}</div>", unsafe_allow_html=True)
            st.markdown("")
            st.markdown("**🔧 Client Version**")
            st.markdown(f"<div style='font-size: 16px;'>{st.session_state.get('client_version', 'N/A')}</div>", unsafe_allow_html=True)
        
        with col2:
            # Mask API key for security
            api_key = st.session_state.get('active_api_key', '')
            masked_key = '*' * len(api_key) if api_key else 'None'
            st.markdown("**🔑 API Key**")
            st.markdown(f"<div style='font-size: 12px;'>{masked_key}</div>", unsafe_allow_html=True)
            st.markdown("")
            st.markdown("**🖥️ Server Version**")
            st.markdown(f"<div style='font-size: 16px;'>{st.session_state.get('server_version', 'N/A')}</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Show active vectorizer keys if any
        active_keys = []
        for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
            if st.session_state.get(f"active_{key}"):
                active_keys.append(key.replace("_key", "").title())
        
        if active_keys:
            st.markdown(f"**🤖 Active Vectorizer Keys:** {', '.join(active_keys)}")
        else:
            st.markdown("**🤖 Active Vectorizer Keys:** None")
        
        # Quick actions
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 Reconfigure", use_container_width=True, type="secondary"):
                st.rerun()
                show_connection_dialog()
        
        with col2:
            if st.button("🔌 Disconnect", use_container_width=True, type="secondary"):
                st.toast('Disconnecting from Weaviate...', icon='🔴')
                if st.session_state.get("client_ready"):
                    close_weaviate_client()
                    clear_session_state()
                    st.rerun()

def initialize_connection_session_state():
    """Initialize connection-related session state variables"""
    # Helper function to safely get secrets with fallback
    def get_secret(key, default=""):
        try:
            return st.secrets.get(key, default)
        except (KeyError, AttributeError):
            return default

    # Initialize custom connection defaults from secrets
    if "custom_http_host" not in st.session_state:
        st.session_state.custom_http_host = get_secret("CUSTOM_HTTP_HOST", "localhost")
    if "custom_http_port" not in st.session_state:
        st.session_state.custom_http_port = int(get_secret("CUSTOM_HTTP_PORT", "8080"))
    if "custom_grpc_host" not in st.session_state:
        st.session_state.custom_grpc_host = get_secret("CUSTOM_GRPC_HOST", "localhost")
    if "custom_grpc_port" not in st.session_state:
        st.session_state.custom_grpc_port = int(get_secret("CUSTOM_GRPC_PORT", "50051"))
    if "custom_secure" not in st.session_state:
        st.session_state.custom_secure = get_secret("CUSTOM_SECURE", "false").lower() == "true"
    if "custom_api_key" not in st.session_state:
        st.session_state.custom_api_key = get_secret("CUSTOM_API_KEY", "")

    # Initialize vectorizer API keys from secrets
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = get_secret("OPENAI_API_KEY", "")
    if "cohere_key" not in st.session_state:
        st.session_state.cohere_key = get_secret("COHERE_API_KEY", "")
    if "jinaai_key" not in st.session_state:
        st.session_state.jinaai_key = get_secret("JINAAI_API_KEY", "")
    if "huggingface_key" not in st.session_state:
        st.session_state.huggingface_key = get_secret("HUGGINGFACE_API_KEY", "")

    # Initialize connection type preference from secrets
    if "use_custom" not in st.session_state or "use_local" not in st.session_state or "use_cloud" not in st.session_state:
        use_local_connection = get_secret("USE_LOCAL_CONNECTION", "false").lower() == "true"
        use_cloud_connection = get_secret("USE_CLOUD_CONNECTION", "false").lower() == "true"
        
        if use_local_connection:
            st.session_state.use_local = True
            st.session_state.use_custom = False
            st.session_state.use_cloud = False
        elif use_cloud_connection:
            st.session_state.use_cloud = True
            st.session_state.use_local = False
            st.session_state.use_custom = False
        else:
            st.session_state.use_custom = True
            st.session_state.use_local = False
            st.session_state.use_cloud = False

    # Initialize remaining session state variables if not already set
    if "local_http_port" not in st.session_state:
        st.session_state.local_http_port = 8080
    if "local_grpc_port" not in st.session_state:
        st.session_state.local_grpc_port = 50051
    if "local_api_key" not in st.session_state:
        st.session_state.local_api_key = ""

    # Cloud connection state
    if "cloud_endpoint" not in st.session_state:
        st.session_state.cloud_endpoint = ""
    if "cloud_api_key" not in st.session_state:
        st.session_state.cloud_api_key = ""
        
    # Active connection state
    if "active_endpoint" not in st.session_state:
        st.session_state.active_endpoint = ""
    if "active_api_key" not in st.session_state:
        st.session_state.active_api_key = ""

    # Connection modal state
    if "show_connection_dialog" not in st.session_state:
        st.session_state.show_connection_dialog = False

def display_connection_form():
    """Display the connection configuration form"""
    
    # Set the default value of connection type
    def local_checkbox_callback():
        if st.session_state.use_local:
            st.session_state.use_custom = False
            st.session_state.use_cloud = False

    def custom_checkbox_callback():
        if st.session_state.use_custom:
            st.session_state.use_local = False
            st.session_state.use_cloud = False

    def cloud_checkbox_callback():
        if st.session_state.use_cloud:
            st.session_state.use_local = False
            st.session_state.use_custom = False

    # Connection type selection
    col1, col2, col3 = st.columns(3)
    with col1:
        use_local = st.checkbox("Local", value=st.session_state.use_local, key='use_local', on_change=local_checkbox_callback)
    with col2:
        use_custom = st.checkbox("Custom", value=st.session_state.use_custom, key='use_custom', on_change=custom_checkbox_callback)
    with col3:
        use_cloud = st.checkbox("☁️ Cloud", value=st.session_state.use_cloud, key='use_cloud', on_change=cloud_checkbox_callback)

    st.divider()

    # Conditional UI based on connection type
    if st.session_state.use_local:
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Local Cluster Endpoint",
                value=f"http://localhost:{st.session_state.local_http_port}",
                disabled=True,
            )
            st.number_input(
                "HTTP Port",
                value=st.session_state.local_http_port,
                key="local_http_port"
            )
        with col2:
            st.number_input(
                "gRPC Port",
                value=st.session_state.local_grpc_port,
                key="local_grpc_port"
            )
            st.text_input(
                "Local Cluster API Key",
                placeholder="Enter Cluster Admin Key",
                type="password",
                value=st.session_state.local_api_key,
                key="local_api_key"
            )
            st.text_input(
                "Custom Cluster API Key",
                placeholder="Enter Cluster Admin Key",
                type="password",
                value=st.session_state.custom_api_key,
                key="custom_api_key"
            )
    elif st.session_state.use_custom:
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Custom HTTP Host",
                placeholder="e.g., localhost",
                value=st.session_state.custom_http_host,
                key="custom_http_host"
            )
            st.text_input(
                "Custom gRPC Host",
                placeholder="e.g., localhost",
                value=st.session_state.custom_grpc_host,
                key="custom_grpc_host"
            )
            st.text_input(
                "Custom Cluster API Key",
                placeholder="Enter Cluster Admin Key",
                type="password",
                value=st.session_state.custom_api_key,
                key="custom_api_key"
            )
        with col2:
            st.number_input(
                "Custom HTTP Port",
                value=st.session_state.custom_http_port,
                key="custom_http_port"
            )
            st.number_input(
                "Custom gRPC Port",
                value=st.session_state.custom_grpc_port,
                key="custom_grpc_port"
            )
            st.checkbox(
                "Use Secure Connection (HTTPS/gRPC)",
                value=st.session_state.custom_secure,
                key="custom_secure"
            )

    elif st.session_state.use_cloud:
        st.info('Connect to a Weaviate Cloud Cluster hosted by Weaviate. You can create clusters at [Weaviate Cloud](https://console.weaviate.cloud/).')
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Cloud Cluster Endpoint",
                placeholder="Enter Cluster Endpoint (URL)",
                value=st.session_state.cloud_endpoint,
                key="cloud_endpoint"
            )
        with col2:
            st.text_input(
                "Cloud Cluster API Key",
                placeholder="Enter Cluster Admin Key",
                type="password",
                value=st.session_state.cloud_api_key,
                key="cloud_api_key"
            )
    
    else:
        st.info("Please select a connection type above.")

    st.divider()
    
    # Vectorizers Integration API Keys Section
    with st.expander("🤖 Model Provider API Keys (Optional)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("OpenAI API Key", type="password", value=st.session_state.openai_key, key="openai_key")
            st.text_input("Cohere API Key", type="password", value=st.session_state.cohere_key, key="cohere_key")
        with col2:
            st.text_input("JinaAI API Key", type="password", value=st.session_state.jinaai_key, key="jinaai_key")
            st.text_input("HuggingFace API Key", type="password", value=st.session_state.huggingface_key, key="huggingface_key")

    st.divider()
    
    # Connect Button
    if st.button("🔗 Connect", use_container_width=True, type="primary"):
        handle_connection()

def handle_connection():
    """Handle the connection logic"""
    close_weaviate_client()

    # Vectorizers Integration API Keys
    vectorizer_integration_keys = {}
    if st.session_state.openai_key:
        vectorizer_integration_keys["X-OpenAI-Api-Key"] = st.session_state.openai_key
    if st.session_state.cohere_key:
        vectorizer_integration_keys["X-Cohere-Api-Key"] = st.session_state.cohere_key
    if st.session_state.jinaai_key:
        vectorizer_integration_keys["X-JinaAI-Api-Key"] = st.session_state.jinaai_key
    if st.session_state.huggingface_key:
        vectorizer_integration_keys["X-HuggingFace-Api-Key"] = st.session_state.huggingface_key

    if st.session_state.use_local:
        if initialize_client(
            use_local=True,
            http_port_endpoint=st.session_state.local_http_port,
            grpc_port_endpoint=st.session_state.local_grpc_port,
            cluster_api_key=st.session_state.local_api_key,
            vectorizer_integration_keys=vectorizer_integration_keys
        ):
            st.success("Local connection successful!")
            # Set active connection info
            st.session_state.active_endpoint = f"http://localhost:{st.session_state.local_http_port}"
            st.session_state.active_api_key = st.session_state.local_api_key
            # Persist the API keys in active_ keys
            for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
                st.session_state[f"active_{key}"] = st.session_state.get(key, "")
            st.session_state.show_connection_dialog = False
            st.rerun()
        else:
            st.error("Connection failed!")
    elif st.session_state.use_custom:
        if initialize_client(
            use_custom=True,
            http_host_endpoint=st.session_state.custom_http_host,
            http_port_endpoint=st.session_state.custom_http_port,
            grpc_host_endpoint=st.session_state.custom_grpc_host,
            grpc_port_endpoint=st.session_state.custom_grpc_port,
            custom_secure=st.session_state.custom_secure,
            cluster_api_key=st.session_state.custom_api_key,
            vectorizer_integration_keys=vectorizer_integration_keys
        ):
            st.success("Custom Connection successful!")
            # Set active connection info
            protocol = "https" if st.session_state.custom_secure else "http"
            st.session_state.active_endpoint = f"{protocol}://{st.session_state.custom_http_host}:{st.session_state.custom_http_port}"
            st.session_state.active_api_key = st.session_state.custom_api_key
            # Persist the API keys in active_ keys
            for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
                st.session_state[f"active_{key}"] = st.session_state.get(key, "")
            st.session_state.show_connection_dialog = False
            st.rerun()
        else:
            st.error("Connection failed!")
    elif st.session_state.use_cloud:
        cloud_endpoint = st.session_state.cloud_endpoint
        if cloud_endpoint and not cloud_endpoint.startswith('https://'):
            cloud_endpoint = f"https://{cloud_endpoint}"

        if not cloud_endpoint or not st.session_state.cloud_api_key:
            st.error("Please insert the cluster endpoint and API key!")
        else:
            if initialize_client(
                cluster_endpoint=cloud_endpoint,
                cluster_api_key=st.session_state.cloud_api_key,
                vectorizer_integration_keys=vectorizer_integration_keys
            ):
                st.success("Cloud Connection successful!")
                # Set active connection info
                st.session_state.active_endpoint = cloud_endpoint
                st.session_state.active_api_key = st.session_state.cloud_api_key
                # Persist the API keys in active_ keys
                for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
                    st.session_state[f"active_{key}"] = st.session_state.get(key, "")
                st.session_state.show_connection_dialog = False
                st.rerun()
            else:
                st.error("Connection failed!")
    else:
        st.error("Please select a connection type before connecting!")

def display_connection_status():
    """Display current connection status and management options"""
    st.subheader("🔗 Connection Status")
    
    if not st.session_state.client_ready:
        st.error("❌ Not connected to Weaviate")
        st.markdown("Configure your Weaviate connection to get started.")
    else:
        st.success(f"✅ Connected to: {st.session_state.active_endpoint}")
        
        # Connection details
        with st.expander("📋 Connection Details", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Endpoint", st.session_state.active_endpoint)
            with col2:
                api_key_display = "*" * len(st.session_state.active_api_key) if st.session_state.active_api_key else "None"
                st.metric("API Key", api_key_display)
            
            # Show active vectorizer keys
            active_keys = []
            for key in ["openai_key", "cohere_key", "jinaai_key", "huggingface_key"]:
                if st.session_state.get(f"active_{key}"):
                    active_keys.append(key.replace("_key", "").title())
            
            if active_keys:
                st.markdown(f"**Active Vectorizer Keys:** {', '.join(active_keys)}")
            else:
                st.markdown("**Active Vectorizer Keys:** None")
        
        # Disconnect button
        if st.button("🔌 Disconnect", use_container_width=True, type="secondary"):
            st.toast('Session, states and cache cleared! Weaviate client disconnected successfully!', icon='🔴')
            time.sleep(1)
            if st.session_state.get("client_ready"):
                message = close_weaviate_client()
                clear_session_state()
                st.rerun()

def show_connection_configuration():
    """Show connection configuration in a container"""
    with st.container():
        display_connection_form()

def show_connections_in_settings():
    """Show connections management within Settings section"""
    # Initialize connection session state
    initialize_connection_session_state()
    
    st.subheader("🔗 Connection Management")
    
    # Connection status section
    display_connection_status()
    
    st.divider()
    
    # Connection configuration section
    st.markdown("**⚙️ Connection Configuration**")
    
    # Toggle for showing connection dialog
    if not st.session_state.client_ready:
        st.markdown("Configure a new connection to get started:")
        if st.button("🔧 Configure Connection", use_container_width=True, type="primary", key="config_conn_settings"):
            show_connection_dialog()
    else:
        if st.button("🔧 Reconfigure Connection", use_container_width=True, key="reconfig_conn_settings"):
            show_connection_dialog()
    
    # Help section
    with st.expander("ℹ️ Connection Help", expanded=False):
        st.markdown("""
        **Connection Types:**
        
        - **Local**: Connect to a Weaviate instance running on your local machine
        - **Custom**: Connect to a Weaviate instance running on a custom host/port
        - **Cloud**: Connect to a Weaviate Cloud cluster
        
        **Model Provider API Keys:**
        
        These are optional and only needed if you plan to use specific vectorizers:
        - **OpenAI**: For text-embedding-ada-002 and other OpenAI models
        - **Cohere**: For Cohere embedding models
        - **JinaAI**: For JinaAI embedding models
        - **HuggingFace**: For HuggingFace embedding models
        
        **Note**: API keys are stored securely in your session and are not persisted.
        """)

def main():
    """Main function for standalone connections page"""
    set_custom_page_config(page_title="Connections")
    navigate()
    
    # Initialize connection session state
    initialize_connection_session_state()
    
    if st.session_state.get("client_ready"):
        update_side_bar_labels()
    
    st.title("🔗 Weaviate Connections")
    st.markdown("Manage your Weaviate database connections and configuration.")
    
    # Use the settings component
    show_connections_in_settings()

if __name__ == "__main__":
    main()