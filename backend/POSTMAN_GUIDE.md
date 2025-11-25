# Postman API Testing Guide

This guide will help you test the Checkmate backend API using Postman.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Testing Authentication](#testing-authentication)
3. [Using JWT Tokens](#using-jwt-tokens)
4. [Testing API Endpoints](#testing-api-endpoints)
5. [Importing the Collection](#importing-the-collection)

## Initial Setup

### 1. Create a New Environment

1. Open Postman
2. Click on **Environments** in the left sidebar
3. Click **+** to create a new environment
4. Name it "Checkmate Local"
5. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `api_url` | `http://localhost:8000/api` | `http://localhost:8000/api` |
| `token` | (leave empty) | (will be set automatically) |

6. Click **Save**

### 2. Set Active Environment

- Select "Checkmate Local" from the environment dropdown (top right)

## Testing Authentication

### Step 1: Sign Up (Create User)

1. Create a new request:
   - Method: **POST**
   - URL: `{{api_url}}/auth/signup`
   - Body tab → **raw** → **JSON**:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "testpassword123"
   }
   ```

2. Click **Send**
3. Expected response (201 Created):
   ```json
   {
     "id": 1,
     "username": "testuser",
     "email": "test@example.com",
     "is_active": true,
     "created_at": "2024-01-01T00:00:00"
   }
   ```

### Step 2: Login (Get JWT Token)

1. Create a new request:
   - Method: **POST**
   - URL: `{{api_url}}/auth/login`
   - Body tab → **raw** → **JSON**:
   ```json
   {
     "username": "testuser",
     "password": "testpassword123"
   }
   ```

2. Click **Send**
3. Expected response (200 OK):
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

### Step 3: Save Token Automatically

1. In the Login request, go to **Tests** tab
2. Add this script:
   ```javascript
   if (pm.response.code === 200) {
       var jsonData = pm.response.json();
       pm.environment.set("token", jsonData.access_token);
       console.log("Token saved:", jsonData.access_token);
   }
   ```

3. Now when you login, the token will be automatically saved to your environment!

## Using JWT Tokens

### Setting Authorization Header

For protected endpoints, you need to include the JWT token:

1. Go to the **Authorization** tab
2. Select **Bearer Token** from the Type dropdown
3. In the Token field, enter: `{{token}}`

Or manually in Headers:
- Key: `Authorization`
- Value: `Bearer {{token}}`

## Testing API Endpoints

### Health Check (No Auth Required)

- **Method**: GET
- **URL**: `{{base_url}}/health`
- **Expected**: `{"status": "healthy"}`

### User Endpoints

#### Get Current User Info
- **Method**: GET
- **URL**: `{{api_url}}/users/me`
- **Auth**: Bearer Token required
- **Expected**: User object

### Trip Endpoints

#### Create Trip
- **Method**: POST
- **URL**: `{{api_url}}/trips`
- **Auth**: Bearer Token required
- **Body** (JSON):
  ```json
  {
    "name": "Summer Vacation 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-15"
  }
  ```
- **Expected**: Trip object with ID

#### List My Trips
- **Method**: GET
- **URL**: `{{api_url}}/trips`
- **Auth**: Bearer Token required
- **Expected**: Array of trip objects

#### Get Trip Details
- **Method**: GET
- **URL**: `{{api_url}}/trips/{trip_id}`
- **Auth**: Bearer Token required
- Replace `{trip_id}` with actual trip ID
- **Expected**: Trip object with participants

#### Invite Participant
- **Method**: POST
- **URL**: `{{api_url}}/trips/{trip_id}/participants`
- **Auth**: Bearer Token required
- **Body** (JSON):
  ```json
  {
    "username": "anotheruser"
  }
  ```

### Expense Endpoints

#### Create Expense
- **Method**: POST
- **URL**: `{{api_url}}/expenses/{trip_id}/{date}`
- **Auth**: Bearer Token required
- Replace `{trip_id}` and `{date}` (format: YYYY-MM-DD)
- **Body** (JSON):
  ```json
  {
    "amount": 50000,
    "currency": "KRW",
    "description": "Lunch at restaurant",
    "category": "Food",
    "participant_ids": [1, 2]
  }
  ```

#### Get Expenses for Date
- **Method**: GET
- **URL**: `{{api_url}}/expenses/{trip_id}/{date}`
- **Auth**: Bearer Token required
- **Expected**: Array of expense objects

### Diary Endpoints

#### Upload Photos
- **Method**: POST
- **URL**: `{{api_url}}/diary/{trip_id}/{date}/photos`
- **Auth**: Bearer Token required
- **Body**: form-data
  - Key: `files` (type: File, select multiple images)
  - Key: `memo` (type: Text, optional)

#### Add/Update Memo
- **Method**: POST
- **URL**: `{{api_url}}/diary/{trip_id}/{date}/memo`
- **Auth**: Bearer Token required
- **Body** (JSON):
  ```json
  {
    "memo": "Had a great day at the beach!"
  }
  ```

### Calendar Endpoints

#### Get Daily Indicators
- **Method**: GET
- **URL**: `{{api_url}}/calendar/{trip_id}/days`
- **Auth**: Bearer Token required
- **Expected**: Array of date indicators

#### Set Mood
- **Method**: POST
- **URL**: `{{api_url}}/calendar/{trip_id}/{date}/mood`
- **Auth**: Bearer Token required
- **Body** (JSON):
  ```json
  {
    "date": "2024-07-05",
    "mood_emoji": "😊"
  }
  ```

### Budget Endpoints

#### Set Budget
- **Method**: POST
- **URL**: `{{api_url}}/budget/{trip_id}`
- **Auth**: Bearer Token required
- **Body** (JSON):
  ```json
  {
    "budget_amount_krw": 1000000
  }
  ```

#### Get Budget Summary
- **Method**: GET
- **URL**: `{{api_url}}/budget/{trip_id}/summary`
- **Auth**: Bearer Token required
- **Expected**: Budget summary with spending details

## Importing the Collection

### Quick Import Steps

1. **Open Postman**
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose `Checkmate_API.postman_collection.json` from the `backend` folder
5. Click **Import**

The collection will appear in your left sidebar with all requests organized in folders.

### After Import

1. **Set up Environment** (if not done already):
   - Create "Checkmate Local" environment as described above
   - Set `base_url` = `http://localhost:8000`
   - Set `api_url` = `http://localhost:8000/api`

2. **Select Environment**:
   - Choose "Checkmate Local" from the environment dropdown

3. **Start Testing**:
   - Run "Login" request first to get a token
   - The token will be automatically saved to your environment
   - All other requests will use this token automatically

### Collection Features

- ✅ **Auto-save Token**: Login request automatically saves JWT token
- ✅ **Auto-save IDs**: Trip and expense IDs are saved after creation
- ✅ **Organized Folders**: Requests grouped by feature
- ✅ **Pre-configured Auth**: All protected endpoints use Bearer token
- ✅ **Test Scripts**: Basic validation tests included

## Tips and Best Practices

### 1. Organize Requests in Folders

Create folders in Postman:
- Authentication
- Trips
- Expenses
- Diary
- Calendar
- Budget
- Settlement

### 2. Use Variables

Instead of hardcoding values:
- Use `{{trip_id}}` variable after creating a trip
- Use `{{expense_id}}` after creating an expense
- Set variables in Tests tab:
  ```javascript
  if (pm.response.code === 201) {
      var jsonData = pm.response.json();
      pm.environment.set("trip_id", jsonData.id);
  }
  ```

### 3. Pre-request Scripts

Add common setup in Pre-request Script tab:
```javascript
// Check if token exists
if (!pm.environment.get("token")) {
    console.log("Warning: No token found. Please login first.");
}
```

### 4. Test Scripts

Add assertions in Tests tab:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has data", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('data');
});
```

### 5. Collection Runner

1. Select your collection
2. Click **Run**
3. Select requests to run
4. Click **Run Checkmate API**
5. View results

## Common Issues

### 401 Unauthorized
- Token expired or missing
- Solution: Login again to get a new token

### 403 Forbidden
- User doesn't have access to the resource
- Solution: Check if user is a participant in the trip

### 404 Not Found
- Invalid endpoint or resource ID
- Solution: Check URL and IDs

### 422 Validation Error
- Invalid request body format
- Solution: Check JSON structure matches schema

## Quick Test Flow

1. **Sign Up** → Create a new user
2. **Login** → Get JWT token (auto-saved)
3. **Create Trip** → Get trip_id (save as variable)
4. **Create Expense** → Add an expense to the trip
5. **Get Expenses** → Verify expense was created
6. **Set Budget** → Set personal budget
7. **Upload Photo** → Add diary photo
8. **Set Mood** → Add mood for a date

## Next Steps

- Import the provided Postman Collection (see below)
- Customize requests for your needs
- Add more test scripts
- Share collection with your team

