# Local Development Setup Guide

This guide will help you set up and run the Checkmate backend locally for testing.

## Prerequisites

1. **Python 3.11+** - Install from [python.org](https://www.python.org/downloads/)
2. **MySQL 8.0** - You can either:
   - Install MySQL locally, OR
   - Use Docker to run only MySQL (recommended for easier setup)

## Option 1: Full Local Setup (MySQL Installed Locally)

### Step 1: Install MySQL

Install MySQL 8.0 on your system and create a database:

```sql
CREATE DATABASE checkmate_db;
CREATE USER 'checkmate_user'@'localhost' IDENTIFIED BY 'checkmate_password';
GRANT ALL PRIVILEGES ON checkmate_db.* TO 'checkmate_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 2: Set Up Python Environment

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Application Settings
APP_NAME=Checkmate
DEBUG=true

# Database (for local MySQL)
DATABASE_URL=mysql+pymysql://checkmate_user:checkmate_password@localhost:3306/checkmate_db
DB_ECHO=false

# JWT
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=app/static

# OCR (optional for local testing)
OCR_SERVICE_URL=http://localhost:8001

# Exchange Rate (optional)
FX_API_KEY=
FX_BASE_CURRENCY=KRW
```

### Step 4: Initialize Database

Run the database initialization script:

```bash
python -m app.db.init_db
```

Or using Python directly:
```bash
python
>>> from app.db.init_db import init_db
>>> init_db()
```

### Step 5: Run the Application

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Option 2: Hybrid Setup (Docker MySQL + Local Python)

This is recommended if you don't want to install MySQL locally.

### Step 1: Start MySQL with Docker

Create a `docker-compose.mysql-only.yml` file:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: checkmate-mysql-local
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=checkmate_db
      - MYSQL_USER=checkmate_user
      - MYSQL_PASSWORD=checkmate_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data_local:/var/lib/mysql

volumes:
  mysql_data_local:
```

Start MySQL:
```bash
docker-compose -f docker-compose.mysql-only.yml up -d
```

### Step 2-5: Follow Steps 2-5 from Option 1

Use the same `.env` file configuration as Option 1, but the database connection will be to `localhost:3306` (which Docker exposes).

## Quick Start Script

You can also create a simple startup script. For Windows, create `start_local.bat`:

```batch
@echo off
echo Starting Checkmate Backend...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For macOS/Linux, create `start_local.sh`:

```bash
#!/bin/bash
echo "Starting Checkmate Backend..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Make it executable:
```bash
chmod +x start_local.sh
```

## Testing the Setup

1. **Check if the server is running:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy"}`

2. **Test API documentation:**
   Open http://localhost:8000/docs in your browser

3. **Test signup endpoint:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "testpassword123"
     }'
   ```

4. **Test login:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "testpassword123"
     }'
   ```

## Troubleshooting

### Database Connection Issues

- **Error: Can't connect to MySQL server**
  - Check if MySQL is running: `mysql -u checkmate_user -p`
  - Verify DATABASE_URL in `.env` matches your MySQL setup
  - Check MySQL is listening on port 3306

### Port Already in Use

- **Error: Address already in use**
  - Change the port: `uvicorn app.main:app --reload --port 8001`
  - Or find and stop the process using port 8000

### Import Errors

- **Error: No module named 'app'**
  - Make sure you're in the `backend` directory
  - Verify your Python path includes the backend directory
  - Try: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` (Linux/Mac) or `set PYTHONPATH=%CD%` (Windows)

### Database Initialization Issues

- **Error: Table already exists**
  - This is normal if you've run init_db before
  - To reset: Drop and recreate the database, then run init_db again

## Development Tips

1. **Auto-reload**: The `--reload` flag enables auto-reload on code changes
2. **Debug mode**: Set `DEBUG=true` in `.env` for detailed error messages
3. **Database inspection**: Use MySQL Workbench or Adminer to inspect the database
4. **API testing**: Use the interactive docs at `/docs` or tools like Postman/Insomnia

## Next Steps

- Create test users and trips
- Test the API endpoints using the interactive documentation
- Set up your frontend to connect to `http://localhost:8000/api`

