# Task Manager Application

A full-stack web application for managing tasks with user authentication and JWT-based security.

## Features

✅ **User Authentication**
- User registration with email validation
- Login with JWT tokens
- Secure password hashing with bcrypt

✅ **Task Management**
- Create, read, update, and delete tasks
- Mark tasks as completed/pending
- Filter tasks by completion status
- Pagination support

✅ **Security**
- JWT-based authentication
- Password hashing with bcrypt
- Secure user isolation (users can only see their own tasks)

## Tech Stack

**Backend:**
- FastAPI 0.68.1
- SQLAlchemy 1.4.46
- Pydantic 1.10.12
- SQLite database

**Frontend:**
- HTML5 + CSS3 + Vanilla JavaScript
- No external dependencies required

**DevOps:**
- Docker & Docker Compose
- Nginx reverse proxy

## Project Structure

```
task_manager/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app and routes
│       ├── database.py       # Database configuration
│       ├── models.py         # SQLAlchemy models
│       ├── schemas.py        # Pydantic models
│       ├── crud.py          # Database operations
│       ├── auth.py          # JWT authentication
│       └── __init__.py
├── frontend/
│   └── index.html           # Single-page application
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Local development setup
├── nginx.conf              # Nginx configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Setup

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker
- Docker Compose

**Steps:**

1. Clone the repository:
```bash
git clone <repository-url>
cd task_manager
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Local Development (Python 3.11+)

**Prerequisites:**
- Python 3.11 or higher
- pip/venv

**Steps:**

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend:
```bash
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Open frontend in browser or serve with HTTP server:
```bash
cd frontend
python -m http.server 3000
```

## Environment Variables

The `.env.example` file shows required variables:

```env
DATABASE_URL=sqlite:///./task_manager.db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important:** Never commit `.env` file to version control.

## API Endpoints

### Authentication

- **POST** `/register` - Register new user
- **POST** `/login` - Login user

### Tasks

- **POST** `/tasks` - Create task (authenticated)
- **GET** `/tasks` - Get all user tasks (supports `?completed=true/false`)
- **GET** `/tasks/{id}` - Get specific task
- **PUT** `/tasks/{id}` - Update task
- **DELETE** `/tasks/{id}` - Delete task

### Documentation

- **GET** `/docs` - Interactive API documentation (Swagger UI)

## Testing

Run pytest tests:

```bash
pytest backend/app/test_main.py -v
```

## Deployment

### Deploy to Render

1. Push code to GitHub (public repository)

2. Create new Web Service on render.com
   - Connect GitHub repository
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`

3. Set environment variables in Render dashboard:
   - `SECRET_KEY` - Generate a secure random key
   - `DATABASE_URL` - Use PostgreSQL for production

### Deploy to Railway

1. Push code to GitHub
2. Create new project on railway.app
3. Connect GitHub repository
4. Railway auto-detects Python
5. Add environment variables in Railway dashboard

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    description VARCHAR,
    completed BOOLEAN DEFAULT FALSE,
    owner_id INTEGER FOREIGN KEY
);
```

## Security Considerations

- JWT tokens expire after 30 minutes (configurable)
- Passwords are hashed using bcrypt
- Users can only access their own tasks
- Use HTTPS in production
- Store `SECRET_KEY` securely in environment

## Troubleshooting

**Port already in use:**
```bash
# Linux/Mac:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
```

**Database locked error:**
- Delete `task_manager.db` and restart

## License

MIT License - Open source

---

Built with FastAPI and Vanilla JavaScript
5. Frontend: open `frontend/index.html` in browser (or serve static)

## API Docs
http://localhost:8000/docs

## Deployment
See Render/Railway instructions below.

## Env Vars
See `.env.example`
