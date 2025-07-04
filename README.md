# WeaviateAdmin - Enhanced Weaviate Cluster Operations

## Overview

WeaviateAdmin is an enhanced version of the Weaviate Cluster Operations tool, providing comprehensive management capabilities for Weaviate Vector Database clusters. This application offers an intuitive web interface to inspect shards, manage collections & tenants, explore schemas, analyze cluster statistics, perform backup operations, and interact with objects.

**Original Project**: This project is based on the excellent work by [Shah91n/WeaviateDBCluster](https://github.com/Shah91n/WeaviateDBCluster). We extend our gratitude to the original author for creating the foundation that made these enhancements possible.

## 🚀 Enhanced Features

### 🔗 Connection Management
- **Local Connection**: Connect to local Weaviate instances
- **Custom Connection**: Connect to custom endpoints with API key support
- **Cloud Connection**: Seamless integration with Weaviate Cloud Services (WCS)
- **Connection Info Dialog**: View active connection details
- **Session Management**: Persistent connection state with disconnect functionality

### 🤖 Advanced Vectorization Support
- **OpenAI Integration**: GPT-based text vectorization
- **Cohere Support**: Enterprise-grade text embeddings
- **HuggingFace Models**: Open-source transformer models
- **JinaAI Integration**: Multilingual embedding models
- **Multi2vec-CLIP**: Multimodal vectorization for text and images
- **API Key Management**: Secure storage and management of vectorization provider credentials
- **Dynamic Vectorization**: Real-time vectorization during object updates

### 🏗️ Cluster Management

#### Shards & Nodes
- **Shard Details**: Comprehensive view of shard distribution across nodes
- **Node Information**: Detailed node status and health monitoring
- **Shard Status Management**: Update read-only shards to READY status (Admin API required)
- **Cluster Topology**: Visual representation of cluster architecture

#### Collections & Tenants
- **Collection Overview**: View all collections with metadata
- **Tenant Management**: Multi-tenant collection support
- **Data Caching**: Performance optimization with intelligent caching
- **Schema Exploration**: Interactive schema configuration viewer
- **Statistics Analysis**: Real-time cluster performance metrics
- **Metadata Inspection**: Cluster modules and configuration details
- **Consistency Checks**: Automated shard consistency analysis
- **Repair Operations**: Force repair collection objects across nodes

### 🔐 Security & Access Control

#### Role-Based Access Control (RBAC)
- **User Management**: View all users and their assigned roles
- **Role Administration**: Comprehensive role and permission management
- **Permission Details**: Granular permission inspection
- **Access Reports**: Users & permissions reporting dashboard

#### Multi-Tenancy Support
- **MT Collections**: Specialized multi-tenant collection management
- **Tenant Analysis**: State monitoring and tenant health checks
- **Configuration Management**: Tenant-specific settings and policies
- **Data Isolation**: Secure tenant data separation

### 📄 Enhanced Document Operations

#### Create Operations (Admin API Required)
- **Collection Creation**: Advanced collection setup with custom properties
- **Vectorizer Configuration**: Support for all major vectorization providers
- **Batch Data Upload**: CSV/JSON file import with validation
- **Multimodal Support**: Text and image processing with Multi2vec-CLIP
- **Schema Validation**: Real-time schema compliance checking

#### Advanced Search Capabilities
- **Hybrid Search**: Intelligent combination of vector and keyword search
- **BM25 Keyword Search**: Precise text matching with relevance scoring
- **Alpha Parameter Control**: Fine-tuned search balance (0.0-1.0)
- **Performance Metrics**: Detailed search timing and scoring analytics
- **Result Metadata**: Comprehensive result information including distances and scores
- **Multi-Collection Support**: Search across all vectorized collections

#### Read Operations
- **Object Visualization**: Tabular display of object data including vectors
- **Data Caching**: Optimized data retrieval with intelligent caching
- **CSV Export**: Download object data in CSV format
- **Pagination Support**: Efficient handling of large datasets
- **Filter Capabilities**: Advanced object filtering and sorting

#### Update Operations (Admin API Required)
- **Collection Configuration**: Edit mutable collection parameters
- **Object Updates**: Modify objects with optional re-vectorization
- **Batch Operations**: Bulk update capabilities
- **Consistency Verification**: Cross-node object consistency checks (up to 11 nodes)
- **Real-time Validation**: Live object validation and error handling
- **Export Functionality**: Object data export with formatting options

#### Delete Operations (Admin API Required)
- **Collection Deletion**: Safe collection removal with confirmation
- **Tenant Management**: Multi-tenant deletion support
- **Batch Deletion**: Efficient bulk deletion operations
- **Cascade Options**: Configurable deletion behavior

### 💾 Comprehensive Backup Management

#### Backup Operations
- **Multi-Provider Support**: Filesystem, AWS S3, Google Cloud Storage, Azure Blob Storage
- **Collection Selection**: Granular backup control with collection filtering
- **Backup Scheduling**: Automated backup creation and management
- **Progress Monitoring**: Real-time backup progress tracking
- **Status Management**: Comprehensive backup status tracking (IN_PROGRESS, SUCCESS, FAILED)

#### Backup History & Metadata
- **Backup History Collection**: Automated metadata storage in Weaviate
- **Detailed Logging**: Comprehensive backup metadata including:
  - Backup ID and provider information
  - Creation and completion timestamps
  - Collection lists and storage paths
  - Size tracking and error messages
  - Status progression and completion times
- **History Visualization**: Tabular display of backup history with sorting
- **Record Management**: Delete outdated backup records

#### Backup Providers
- **Filesystem**: Local storage for development and testing
- **AWS S3**: Production-ready cloud storage with multi-node support
- **Google Cloud Storage**: GCP-native storage solution
- **Azure Blob Storage**: Microsoft Azure integration
- **Configuration Guidance**: Environment variable setup instructions

### 🎨 User Interface Enhancements
- **Modern Design**: Clean, intuitive interface with consistent styling
- **Responsive Layout**: Optimized for various screen sizes
- **Interactive Components**: Enhanced user experience with dynamic elements
- **Status Indicators**: Visual feedback for operations and system status
- **Error Handling**: Comprehensive error messages and recovery suggestions
- **Loading States**: Progress indicators for long-running operations

### 🔧 Technical Improvements
- **Enhanced Error Handling**: Robust error management with detailed logging
- **Performance Optimization**: Efficient data loading and caching strategies
- **Code Organization**: Modular architecture with clear separation of concerns
- **Session Management**: Persistent state management across page navigation
- **API Compatibility**: Support for latest Weaviate API versions
- **Memory Management**: Optimized resource usage and cleanup

## 📋 Requirements

- **Python**: 3.10 or higher
- **Dependencies**: See `requirements.txt`
  - `streamlit`: Web application framework
  - `weaviate-client`: Official Weaviate Python client
  - `requests`: HTTP library for API calls
  - `pandas`: Data manipulation and analysis
  - `Pillow`: Image processing for multimodal support

## 🚀 Installation & Setup

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd WeaviateAdmin
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Access the application:**
   Open your browser and navigate to `http://localhost:8501`

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t weaviateadmin:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 --add-host=localhost:host-gateway weaviateadmin
   ```

### Cloud Deployment

1. **Configure your Weaviate endpoint**
2. **Provide API key for authentication**
3. **Connect and start managing your cluster**

## 🔧 Configuration

### Environment Variables

For backup functionality, configure the following environment variables in your Weaviate deployment:

#### Filesystem Backup
```bash
BACKUP_FILESYSTEM_PATH=/path/to/backup/directory
```

#### AWS S3 Backup
```bash
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_PATH=backup/path
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=your-region
```

#### Google Cloud Storage
```bash
BACKUP_GCS_BUCKET=your-backup-bucket
BACKUP_GCS_PATH=backup/path
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Azure Blob Storage
```bash
BACKUP_AZURE_CONTAINER=your-container
BACKUP_AZURE_PATH=backup/path
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

## 🛡️ Security Considerations

- **Admin Operations**: Many features require Admin API keys for security
- **API Key Management**: Secure storage and handling of authentication credentials
- **Access Control**: RBAC integration for user permission management
- **Data Isolation**: Multi-tenant data separation and security
- **Audit Logging**: Comprehensive operation logging for security monitoring

## 🤝 Contributing

We welcome contributions to enhance WeaviateAdmin! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**
3. **Implement your changes**
4. **Add tests if applicable**
5. **Submit a pull request**

### Development Guidelines
- Follow Python best practices and PEP 8 style guidelines
- Add comprehensive error handling
- Include documentation for new features
- Test thoroughly with different Weaviate configurations

## 📝 License

This project maintains the same license as the original [WeaviateDBCluster](https://github.com/Shah91n/WeaviateDBCluster) project.

## 🙏 Acknowledgments

- **Original Author**: [Shah91n](https://github.com/Shah91n) for creating the foundational WeaviateDBCluster project
- **Weaviate Team**: For developing the excellent Weaviate vector database
- **Streamlit Team**: For providing the web application framework
- **Community Contributors**: For feedback, suggestions, and improvements

## ⚠️ Important Notes

- **Version Compatibility**: This tool is designed and tested with the latest Weaviate DB version
- **Production Use**: While functional, use at your own risk in production environments
- **Backup Testing**: Always test backup and restore procedures in non-production environments
- **API Requirements**: Some features require Admin API keys for security reasons

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Refer to inline help and tooltips
- **Community**: Join the Weaviate community for discussions

---

**Note**: This is an enhanced community project and is not officially endorsed by Weaviate. While we strive for reliability and best practices, please use responsibly and test thoroughly in your environment.
