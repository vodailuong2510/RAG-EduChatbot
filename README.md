# RAG-EduChatbot 🤖

EduChatbot with RAG (Retrieval-Augmented Generation) is an intelligent chatbot leveraging LLMs and RAG to provide accurate and efficient academic regulation guidance for UIT students and faculty.

## 🌟 Key Features

- **Intelligent Chat**: Natural interaction in Vietnamese
- **RAG-powered**: Accurate information retrieval from regulatory documents
- **Chat Management**: Store and manage conversation history
- **User Authentication**: Login system and role-based access control
- **Web Interface**: User-friendly and responsive UI
- **Admin Panel**: System management for administrators

## 🏗️ System Architecture

```
RAG-EduChatbot/
├── server.py              # Main FastAPI server
├── auth_routes.py         # Authentication handling
├── admin_routes.py        # Admin management
├── chat/                  # Chat processing module
│   ├── response.py        # Chat logic with OpenAI
│   ├── utils.py           # Chat utilities
│   └── thinking.py        # Thinking processing
├── database/              # Database layer
│   ├── mongodb.py         # MongoDB connection
│   ├── weaviatedb.py      # Weaviate vector DB
│   └── retrieve.py        # RAG retrieval
├── reader/                # Document processing
│   ├── reader.py          # Document reader
│   └── scraper.py         # Web scraping
├── data/                  # Data storage
│   ├── documents/         # Raw documents
│   └── csv/              # Training data
├── templates/             # HTML templates
├── static/               # CSS/JS assets
└── docker-compose.*.yml  # Docker configurations
```

## 🛠️ Technologies Used

### Backend
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **PyJWT**: JWT authentication
- **OAuth**: OAuth authentication
- **OpenAI**: LLM integration

### Database
- **MongoDB**: Chat history & user management
- **Weaviate**: Vector database for RAG

### AI/ML
- **Sentence Transformers**: Text embeddings
- **LlamaIndex**: Document processing
- **Transformers**: NLP models

### Infrastructure
- **Docker**: Containerization
- **Python 3.10**: Runtime environment

## 🚀 Installation and Setup

### System Requirements
- Python 3.10+
- Docker & Docker Compose
- MongoDB
- Weaviate

### Method 1: Using Docker (Recommended)

1. **Clone repository**
```bash
git clone <repository-url>
cd RAG-EduChatbot
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with necessary information
```

3. **Run with Docker Compose**
```bash
# Run MongoDB
docker-compose -f docker-compose.mongodb.yml up -d

# Run Weaviate
docker-compose -f docker-compose.weaviate.yml up -d

# Build and run application
docker build -t rag-educhatbot .
docker run -p 8000:8000 --env-file .env rag-educhatbot
```

### Method 2: Local Installation

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure databases**
```bash
# Start MongoDB and Weaviate
# Update connection strings in .env
```

4. **Run application**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## ⚙️ Configuration

Create a `.env` file with the following environment variables:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# MongoDB
MONGO_URI=mongodb://localhost:27017/educhatbot

# Weaviate
WEAVIATE_URL=http://localhost:8080

# JWT
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256

# Application
DEBUG=True
```

## 📚 Usage

### 1. Access the application
- Open browser and navigate to: `http://localhost:8000`
- Login with admin account or create new account

### 2. Chat with bot
- Send questions about academic regulations
- Bot will search information from documents and respond
- Chat history is automatically saved

### 3. Admin management
- Access `/admin` to manage system
- Upload new documents
- Manage users

## 🔧 Development

### Project Structure
- **server.py**: Application entry point
- **auth_routes.py**: Authentication handling
- **admin_routes.py**: Admin functionality
- **chat/**: Chat logic module
- **database/**: Database operations
- **reader/**: Document processing

### API Endpoints
- `GET /`: Redirect to chat or login
- `POST /chat`: Send message to chatbot
- `GET /chats`: Get user's chat history
- `POST /chats/new`: Create new chat
- `GET /admin`: Admin panel
- `GET /account`: User account management

### Adding new documents
1. Upload files to `data/documents/raw/`
2. Run document processing script
3. Index to Weaviate vector database

## 🐳 Docker

### Build image
```bash
docker build -t rag-educhatbot .
```

### Run container
```bash
docker run -p 8000:8000 --env-file .env rag-educhatbot
```

### Docker Compose
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

### Health Check
- Endpoint: `GET /health`
- Automatic Docker health check
- Monitor logs with `docker logs`

### Logs
```bash
# Application logs
docker logs rag-educhatbot

# MongoDB logs
docker logs mongodb

# Weaviate logs
docker logs weaviate
```

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

- **Project Link**: [https://github.com/your-username/RAG-EduChatbot](https://github.com/your-username/RAG-EduChatbot)
- **Email**: vodailuong2510@gmail.com

## 🙏 Acknowledgments

- OpenAI for GPT models
- Weaviate for vector database
- FastAPI for web framework
- UIT for academic regulation documents
