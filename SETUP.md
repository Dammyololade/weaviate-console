# WeactivateAdmin Setup Guide

## Quick Start

### Using the Run Script (Recommended)

1. **Make the script executable** (if not already done):
   ```bash
   chmod +x run.sh
   ```

2. **Run the application**:
   ```bash
   ./run.sh
   ```

The script will automatically:
- Create a virtual environment if it doesn't exist
- Install all required dependencies
- Check for Streamlit secrets configuration
- Start the Streamlit application

### Manual Setup

If you prefer to set up manually:

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Configuration

### Streamlit Secrets Configuration

The application uses Streamlit's built-in secrets management for secure configuration. This approach works both locally and when deployed to Streamlit Cloud.

#### For Local Development

1. **Copy the template secrets file**:
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml` with your actual values**:
   ```toml
   # Weaviate Custom Connection Configuration
   CUSTOM_HTTP_HOST = "localhost"
   CUSTOM_HTTP_PORT = "8080"
   CUSTOM_GRPC_HOST = "localhost"
   CUSTOM_GRPC_PORT = "50051"
   CUSTOM_SECURE = "false"
   CUSTOM_API_KEY = "your_api_key_here"
   
   # Vectorizer API Keys (optional)
   OPENAI_API_KEY = "your_openai_key"
   COHERE_API_KEY = "your_cohere_key"
   JINAAI_API_KEY = "your_jinaai_key"
   HUGGINGFACE_API_KEY = "your_huggingface_key"
   
   # Set to true to use custom connection by default
   USE_CUSTOM_CONNECTION = "true"
   ```

#### For Streamlit Cloud Deployment

1. **Deploy your app to Streamlit Cloud**
2. **Go to your app's settings in the Streamlit Cloud dashboard**
3. **Navigate to the "Secrets" section**
4. **Add the same configuration in TOML format**:
   ```toml
   CUSTOM_HTTP_HOST = "your_weaviate_host"
   CUSTOM_HTTP_PORT = "8080"
   CUSTOM_API_KEY = "your_api_key"
   OPENAI_API_KEY = "your_openai_key"
   # ... add other secrets as needed
   ```

### Configuration Options

- **CUSTOM_HTTP_HOST**: Weaviate HTTP host (default: localhost)
- **CUSTOM_HTTP_PORT**: Weaviate HTTP port (default: 8080)
- **CUSTOM_GRPC_HOST**: Weaviate gRPC host (default: localhost)
- **CUSTOM_GRPC_PORT**: Weaviate gRPC port (default: 50051)
- **CUSTOM_SECURE**: Use HTTPS/secure gRPC (default: false)
- **CUSTOM_API_KEY**: Your Weaviate cluster API key
- **USE_CUSTOM_CONNECTION**: Automatically select custom connection (default: true)

### Vectorizer Integration

Add API keys for various AI model providers:
- **OPENAI_API_KEY**: For OpenAI embeddings
- **COHERE_API_KEY**: For Cohere embeddings
- **JINAAI_API_KEY**: For JinaAI embeddings
- **HUGGINGFACE_API_KEY**: For HuggingFace embeddings
- **Multi2vec-CLIP**: No API key required - uses local inference

#### Multi2vec-CLIP Requirements

For multimodal collections using Multi2vec-CLIP:
- Weaviate instance must have the `multi2vec-clip` module enabled
- CLIP inference container must be running
- Data must include specific fields: `title`, `description` (text), and `image` (base64 blob)
- No API key configuration needed - uses local inference

## Access

Once running, the application will be available at:
- **Local**: http://localhost:8501
- **Network**: http://[your-ip]:8501

## Features

- ✅ Secure configuration using Streamlit secrets
- ✅ Custom Weaviate connection support
- ✅ Multiple vectorizer integrations
- ✅ CRUD operations for collections and objects
- ✅ Search functionality (hybrid and keyword)
- ✅ Multi-tenancy support
- ✅ RBAC (Role-Based Access Control)
- ✅ Cluster operations and monitoring