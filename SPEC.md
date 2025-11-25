1. Overview
A web-based backend application supporting group travel management including shared expenses, personal budgets, OCR-based expense extraction, diaries with photos/memos, calendar views with moods, and automated fair settlement.

Key Features:

• Group trip creation and participant management

• Expense tracking with OCR import and currency normalization (base KRW)

• Shared diary & photo timeline with per-date memos and extra photos

• Calendar with linked moods, expenses, diary entries, and indicators

• Personal budget tracking on “My Page”

• Secure login and persistent session management

• Automated settlement calculation after trip ends

2. Technology Stack
• Component	Specification
• Language	Python 3.x
• Framework	FastAPI
• Database	MySQL
• ORM	SQLAlchemy 2.x
• Authentication	JWT-based session with local token
• Deployment	Docker, Docker Compose
• OCR	Custom Python OCR service
• Base Currency	KRW (daily FX conversion)
• Platform	Responsive web (mobile-first)
• Code Language	English (UI and codebase)

3. System Architecture
Suggested Folder Structure
text
backend/
│
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── core/
│   │   ├── config.py          # Environment & settings
│   │   ├── security.py        # JWT, password hashing
│   │   └── utils.py
│   │
│   ├── db/
│   │   ├── base.py            # Base SQLAlchemy models
│   │   ├── session.py         # DB sessions setup
│   │   └── init_db.py
│   │
│   ├── models/                # SQLAlchemy models per entity
│   │   ├── user.py
│   │   ├── trip.py
│   │   ├── expense.py
│   │   ├── diary.py
│   │   ├── exchange_rate.py
│   │   ├── mood.py
│   │   ├── budget.py
│   │   └── settlement.py
│   │
│   ├── schemas/               # Pydantic models
│   │   ├── user.py
│   │   ├── trip.py
│   │   ├── expense.py
│   │   ├── diary.py
│   │   ├── budget.py
│   │   ├── exchange_rate.py
│   │   ├── mood.py
│   │   └── settlement.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── trips.py
│   │   │   ├── expenses.py
│   │   │   ├── diary.py
│   │   │   ├── budget.py
│   │   │   ├── settlements.py
│   │   │   └── ocr.py
│   │   └── router.py
│   │
│   ├── services/              # Business logic implementations
│   │   ├── settlement_service.py
│   │   ├── expense_service.py
│   │   ├── ocr_service.py
│   │   ├── fx_service.py
│   │   └── diary_service.py
│   │
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_expense.py
│   │   └── test_trip.py
│   │
│   └── static/                # Temporary uploads (images etc.)
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

4. Core Entities and Relationships
Entity	Description
•User	Registered user with immutable unique username
•Trip	Travel event with start/end dates
•Expense	Single spending event, linked to payer and participants
•ExpenseParticipant	Many-to-many junction of Expense and User
•ExchangeRate	Daily currency to KRW conversion rates
•DiaryEntry	Photo/memo per date, either linked to expense or standalone
•DateMood	One mood emoji per user per date
•MyBudget	User’s personal budget per trip
•SettlementResult	Metadata and results of trip settlement
•Relationships:

One User → many Trips (via participation)

One Trip → many Expenses, DiaryEntries, ExchangeRates, SettlementResults

One Expense → many ExpenseParticipants

DiaryEntries may link to an Expense or stand alone

One User → one MyBudget per trip

5. Authentication and Session
• POST /auth/signup: register new user (username immutable)

• POST /auth/login: login and get JWT token

• POST /auth/logout: invalidate current token

• Persistent login through local storage/session token


6. Core Feature Modules & APIs
6.1 Home Tab — Trip Management
• POST /trips: create trip with name, start_date, end_date

• GET /trips: list user’s trips

• GET /trips/{trip_id}: trip details (participants, dates, status)

• POST /trips/{trip_id}/participants: invite participant by username
-> the user who got invitement should press okay button to be invited

• DELETE /trips/{trip_id}/participants/{username}: remove participant

• POST /trips/{trip_id}/set_current: set trip as current

• GET /trips/{trip_id}/status: current trip status (Upcoming/Ongoing/Finished)

• POST /trips/{trip_id}/settle: press settlement button

• GET /trips/{trip_id}/settlement: get settlement result

• GET /trips/{trip_id}/participants: participant list with settlement states

6.2 Image Feed Tab
• GET /trips/{trip_id}/feed?offset=n&limit=10: photo feed (latest first, infinite scroll)

Photo limit: 50 per trip, oldest auto-deleted

• GET /photos/{photo_id}: photo detail (fullscreen, zoom/swipe)

6.3 Calendar Tab — Daily View
•GET /calendar/{trip_id}/days: daily indicators (expenses, diary, moods)

• GET /calendar/{trip_id}/{date}: daily full data (expenses, diary photos, memos, moods)

• POST /calendar/{trip_id}/{date}/mood: set/update mood emoji

Expense Management:

• GET /expenses/{trip_id}/{date}

• POST /expenses/{trip_id}/{date} (manual add)

• POST /expenses/{trip_id}/{date}/ocr (upload for OCR parsing)

• PUT /expenses/{expense_id}, DELETE /expenses/{expense_id}

Exchange Rate Lookup: GET /fx-rates/{date}

OCR import workflow with preview and final save

6.4 Diary: Photos & Memo
• GET /diary/{trip_id}/{date}: diary entry with expense timeline + photos + daily memo

• Photo Management:

• POST /diary/{trip_id}/{date}/photos (upload photos, max 5 per user/date, optional memo)

• PUT /diary/photos/{photo_id} (edit photo memo/metadata)

• DELETE /diary/photos/{photo_id}

Daily Memo:

• POST /diary/{trip_id}/{date}/memo (add or update)

• DELETE /diary/memo/{memo_id}

6.5 My Page — Personal Budget
• GET /budget/{trip_id}: current budget & spending

• POST /budget/{trip_id}: set or edit budget

• GET /budget/{trip_id}/summary: detailed spending, remaining, fill ratio

6.6 Settlement APIs
• POST /settlement/{trip_id}/trigger: run settlement calculation

• GET /settlement/{trip_id}/result: retrieve settlement summary

6.7 OCR APIs
• POST /ocr/parse: upload images for expense line parsing, return provisional data


7. Exchange Rate Management
Daily FX rates ingested via Google API or other ways

Stored as ExchangeRate(date, currency, rate_to_KRW)

Used for real-time conversion on expense creation

8. Settlement Algorithm Logic
Triggered when all participants press settle for finished trip

Calculate each user’s net balance (paid − owed)

Minimize transfer count with debt settlement algorithm

Save results to SettlementResult entity

Mark Trip as settled

9. Docker Configuration
Base image: python:3.11-slim with Uvicorn & FastAPI

docker-compose services:

backend (FastAPI), mysql (MySQL 8), ocr (optional), adminer (optional)

Environment variables stored in .env

10. Security & Validation
Unique, immutable usernames

Token expiry configurable (e.g., 7 days)

All API routes under /api protected by JWT except for login/signup

Trip-level access enforcement (only participants allowed)

Uploaded files validated for type and size

Consistent error response patterns and pagination