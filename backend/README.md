# Checkmate Backend

Backend API for group travel management application with shared expenses, diaries, and automated settlement.

## Features

- Group trip creation and participant management
- Expense tracking with OCR import and currency normalization (base KRW)
- Shared diary & photo timeline with per-date memos
- Calendar with linked moods, expenses, and diary entries
- Personal budget tracking
- Secure JWT-based authentication
- Automated fair settlement calculation

## Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy 2.x
- **Authentication**: JWT
- **Deployment**: Docker, Docker Compose

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── core/                # Core configuration and utilities
│   ├── db/                  # Database setup and session management
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── tests/               # Test files
│   └── static/              # Uploaded files storage
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Create a `.env` file with your configuration:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://checkmate_user:checkmate_password@mysql:3306/checkmate_db
DEBUG=false
FX_API_KEY=your-fx-api-key
```

3. Build and start the services:
```bash
docker-compose up -d
```

4. Initialize the database:
```bash
docker-compose exec backend python -m app.db.init_db
```

5. Access the API:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Adminer (DB admin): http://localhost:8080

### Local Development

For detailed local setup instructions, see [LOCAL_SETUP.md](LOCAL_SETUP.md).

**Quick Start:**

1. **Option A: Use the startup script (recommended)**
   - Windows: `start_local.bat`
   - macOS/Linux: `chmod +x start_local.sh && ./start_local.sh`

2. **Option B: Manual setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up MySQL (or use docker-compose.mysql-only.yml)
   # Create .env file (see LOCAL_SETUP.md)
   
   # Initialize database
   python -m app.db.init_db
   
   # Run server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Access the API:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout

### Trips
- `POST /api/trips` - Create trip
- `GET /api/trips` - List user's trips
- `GET /api/trips/{trip_id}` - Get trip details
- `POST /api/trips/{trip_id}/participants` - Invite participant
- `DELETE /api/trips/{trip_id}/participants/{username}` - Remove participant
- `POST /api/trips/{trip_id}/settle` - Trigger settlement

### Expenses
- `GET /api/expenses/{trip_id}/{date}` - Get expenses for date
- `POST /api/expenses/{trip_id}/{date}` - Create expense
- `POST /api/expenses/{trip_id}/{date}/ocr` - Upload image for OCR
- `PUT /api/expenses/{expense_id}` - Update expense
- `DELETE /api/expenses/{expense_id}` - Delete expense

### Diary
- `GET /api/diary/{trip_id}/{date}` - Get diary entry
- `POST /api/diary/{trip_id}/{date}/photos` - Upload photos
- `POST /api/diary/{trip_id}/{date}/memo` - Add/update memo

### Calendar
- `GET /api/calendar/{trip_id}/days` - Get daily indicators
- `GET /api/calendar/{trip_id}/{date}` - Get daily full data
- `POST /api/calendar/{trip_id}/{date}/mood` - Set mood

### Budget
- `GET /api/budget/{trip_id}` - Get budget
- `POST /api/budget/{trip_id}` - Set/update budget
- `GET /api/budget/{trip_id}/summary` - Get budget summary

### Settlement
- `POST /api/settlement/{trip_id}/trigger` - Trigger settlement
- `GET /api/settlement/{trip_id}/result` - Get settlement result

## Testing

Run tests with pytest:
```bash
pytest app/tests/
```

## Environment Variables

- `SECRET_KEY`: Secret key for JWT tokens
- `DATABASE_URL`: MySQL database connection string
- `DEBUG`: Enable debug mode (true/false)
- `FX_API_KEY`: API key for exchange rate service
- `OCR_SERVICE_URL`: URL for OCR service
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

## License

[Your License Here]

