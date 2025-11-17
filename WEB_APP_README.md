# 🚀 Weapon Detection Web Application

A full-stack web application for real-time weapon detection using YOLO and Faster R-CNN models, built with FastAPI backend and React frontend.

## ✨ Features

### Backend (FastAPI)
- 🔐 **JWT Authentication** - Secure user registration and login
- 🎯 **Dual Model Support** - YOLOv8m and Faster R-CNN detection
- 📊 **REST API** - Complete API for detection, alerts, and analytics
- 💾 **MongoDB Integration** - Store alerts and user data
- ⚡ **Async Processing** - Fast and efficient request handling
- 📈 **Real-time Statistics** - Alert analytics and trends

### Frontend (React + Vite)
- 🎨 **Modern UI** - Beautiful dark-themed interface with Tailwind CSS
- 📱 **Responsive Design** - Works on desktop and mobile
- 🖼️ **Image Upload & Detection** - Drag-and-drop image analysis
- 📊 **Interactive Charts** - Visualize detection statistics
- 🔔 **Alert History** - View and filter all alerts
- ⚙️ **Model Selection** - Choose between YOLO and Faster R-CNN

## 🏗️ Architecture

```
weapon-detection/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   └── endpoints/
│   │   │       ├── auth.py    # Authentication
│   │   │       ├── detection.py # Detection API
│   │   │       └── alerts.py  # Alerts API
│   │   ├── core/              # Core configurations
│   │   │   ├── config.py      # Settings
│   │   │   ├── security.py    # JWT & password hashing
│   │   │   └── database.py    # MongoDB connection
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   └── detection_service.py
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   └── Layout.jsx
│   │   ├── pages/             # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Detection.jsx
│   │   │   ├── Alerts.jsx
│   │   │   └── Analytics.jsx
│   │   ├── services/          # API calls
│   │   │   └── api.js
│   │   ├── store/             # State management
│   │   │   └── authStore.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml         # Docker orchestration
├── dataset/                   # Training dataset
├── runs/                      # Model weights and results
└── src/                       # Original scripts (Streamlit, etc.)
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
cd C:\Workspace\weapon-detection
```

2. **Set up environment variables**
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and set your SECRET_KEY
```

3. **Start all services with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### Option 2: Local Development

#### Backend Setup

1. **Create virtual environment**
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install MongoDB and Redis**
- MongoDB: https://www.mongodb.com/try/download/community
- Redis: https://redis.io/download (or use Docker)

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env file
```

5. **Run backend**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

1. **Install Node.js** (https://nodejs.org/)

2. **Install dependencies**
```bash
cd frontend
npm install
```

3. **Run frontend**
```bash
npm run dev
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

#### Detection
- `POST /api/v1/detection/detect/image` - Upload and detect weapons
- `GET /api/v1/detection/models` - Get available models

#### Alerts
- `GET /api/v1/alerts/` - Get all alerts (with filters)
- `GET /api/v1/alerts/stats` - Get alert statistics
- `GET /api/v1/alerts/{id}` - Get specific alert
- `DELETE /api/v1/alerts/{id}` - Delete alert (admin only)

## 🎯 Usage

### 1. Register/Login
- Navigate to http://localhost:3000
- Register a new account or login
- You'll be redirected to the dashboard

### 2. Upload Image for Detection
- Go to "Detection" page
- Select model (YOLO or Faster R-CNN)
- Adjust confidence threshold
- Upload an image
- Click "Detect Weapons"
- View results with bounding boxes

### 3. View Alerts
- Go to "Alerts" page
- Filter by weapon type or danger level
- View detailed information about each alert

### 4. Analytics
- Go to "Analytics" page
- View charts and statistics
- Change time period (7/30/90 days)

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:
```env
# Security
SECRET_KEY=your-super-secret-key-min-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=weapon_detection

# Redis
REDIS_URL=redis://localhost:6379

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Frontend Configuration

Edit `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild containers
docker-compose up -d --build

# View running containers
docker ps
```

## 🛠️ Development

### Backend Development
```bash
cd backend
# Activate virtual environment
venv\Scripts\Activate.ps1

# Run with auto-reload
python -m uvicorn app.main:app --reload

# Run tests (if available)
pytest
```

### Frontend Development
```bash
cd frontend
npm run dev     # Development server
npm run build   # Production build
npm run preview # Preview production build
```

## 📦 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Motor** - Async MongoDB driver
- **PyTorch** - Deep learning framework
- **Ultralytics YOLO** - Object detection
- **Python-JOSE** - JWT tokens
- **Passlib** - Password hashing

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React Router** - Routing
- **Lucide React** - Icons

### Infrastructure
- **Docker** - Containerization
- **MongoDB** - Database
- **Redis** - Caching
- **Nginx** - Reverse proxy (production)

## 🚧 Troubleshooting

### Backend Issues

**Models not found:**
```bash
# Ensure model weights exist
ls runs/detect/weapons_yolov8_optimized_stable/weights/best.pt
ls runs/models/fasterrcnn_quick_test.pth
```

**MongoDB connection failed:**
```bash
# Check MongoDB is running
docker ps | grep mongo
# Or check local service
sc query MongoDB
```

### Frontend Issues

**API connection failed:**
- Check `frontend/.env` has correct API URL
- Ensure backend is running on port 8000
- Check CORS settings in backend

**Build errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📈 Performance

- **YOLOv8m**: ~20-30ms inference on RTX 3050
- **Faster R-CNN**: ~50-100ms inference on RTX 3050
- **API Response**: <200ms average
- **Frontend Load**: <1s initial load

## 🔒 Security

- JWT token authentication
- Bcrypt password hashing
- CORS configuration
- Rate limiting (can be added)
- Input validation with Pydantic
- XSS protection
- CSRF tokens (for forms)

## 📄 License

MIT License - see LICENSE file for details

## 👥 Contributors

- **Your Name** - Initial work

## 🙏 Acknowledgments

- YOLO by Ultralytics
- Faster R-CNN by Facebook Research
- FastAPI documentation
- React community

---

**Made with ❤️ using FastAPI + React**
