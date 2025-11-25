# API Testing Order Guide for Postman

This guide provides the recommended order for testing all Checkmate API endpoints in Postman.

## Prerequisites

1. ✅ FastAPI server is running (`uvicorn app.main:app --reload`)
2. ✅ MySQL database is running and initialized
3. ✅ Postman collection is imported
4. ✅ Environment is set up with `base_url` and `api_url`

---

## Testing Order

### Phase 1: Setup & Authentication

#### 1. Health Check
**Endpoint:** `GET /health`
- **Purpose:** Verify server is running
- **Expected:** `{"status": "healthy"}`
- **No Auth Required**

#### 2. Sign Up (Create User)
**Endpoint:** `POST /api/auth/signup`
- **Purpose:** Create a new user account
- **Body:**
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
  }
  ```
- **Expected:** 201 Created with user data
- **No Auth Required**
- **Note:** Save the username for later steps

#### 3. Login
**Endpoint:** `POST /api/auth/login`
- **Purpose:** Get JWT token (auto-saved to environment)
- **Body:**
  ```json
  {
    "username": "testuser",
    "password": "testpassword123"
  }
  ```
- **Expected:** 200 OK with `access_token`
- **No Auth Required**
- **Important:** Token is automatically saved to `{{token}}` variable

---

### Phase 2: User Management

#### 4. Get Current User
**Endpoint:** `GET /api/users/me`
- **Purpose:** Verify authentication works
- **Expected:** 200 OK with user data
- **Auth Required:** ✅ Bearer Token

---

### Phase 3: Trip Management

#### 5. Create Trip
**Endpoint:** `POST /api/trips`
- **Purpose:** Create a new trip
- **Body:**
  ```json
  {
    "name": "Summer Vacation 2024",
    "start_date": "2024-07-01",
    "end_date": "2024-07-15"
  }
  ```
- **Expected:** 201 Created with trip data
- **Auth Required:** ✅ Bearer Token
- **Note:** Trip ID is auto-saved to `{{trip_id}}`

#### 6. List Trips
**Endpoint:** `GET /api/trips`
- **Purpose:** See all trips for current user
- **Expected:** 200 OK with array of trips
- **Auth Required:** ✅ Bearer Token

#### 7. Get Trip Details
**Endpoint:** `GET /api/trips/{{trip_id}}`
- **Purpose:** Get full trip information with participants
- **Expected:** 200 OK with trip details
- **Auth Required:** ✅ Bearer Token

#### 8. Get Trip Status
**Endpoint:** `GET /api/trips/{{trip_id}}/status`
- **Purpose:** Check trip status (Upcoming/Ongoing/Finished)
- **Expected:** 200 OK with status
- **Auth Required:** ✅ Bearer Token

#### 9. Invite Participant (Optional)
**Endpoint:** `POST /api/trips/{{trip_id}}/participants`
- **Purpose:** Add another user to the trip
- **Body:**
  ```json
  {
    "username": "anotheruser"
  }
  ```
- **Expected:** 201 Created
- **Auth Required:** ✅ Bearer Token
- **Note:** Requires another user to exist (create via signup first)

#### 10. Get Participants
**Endpoint:** `GET /api/trips/{{trip_id}}/participants`
- **Purpose:** List all trip participants
- **Expected:** 200 OK with participant list
- **Auth Required:** ✅ Bearer Token

---

### Phase 4: Expense Management

#### 11. Create Expense
**Endpoint:** `POST /api/expenses/{{trip_id}}/2024-07-05`
- **Purpose:** Add an expense for a specific date
- **Body:**
  ```json
  {
    "amount": 50000,
    "currency": "KRW",
    "description": "Lunch at restaurant",
    "category": "Food",
    "participant_ids": [1]
  }
  ```
- **Expected:** 201 Created with expense data
- **Auth Required:** ✅ Bearer Token
- **Note:** Expense ID is auto-saved to `{{expense_id}}`
- **Tip:** Use a date within your trip's date range

#### 12. Get Expenses by Date
**Endpoint:** `GET /api/expenses/{{trip_id}}/2024-07-05`
- **Purpose:** Retrieve all expenses for a specific date
- **Expected:** 200 OK with array of expenses
- **Auth Required:** ✅ Bearer Token

#### 13. Update Expense
**Endpoint:** `PUT /api/expenses/{{expense_id}}`
- **Purpose:** Modify an existing expense
- **Note:** All fields are optional - only include fields you want to update
- **Updatable Fields:**
  - `amount` - Change expense amount
  - `currency` - Change currency (USD, EUR, KRW, etc.)
  - `description` - Update expense description
  - `category` - Change expense category
  - `participant_ids` - Update list of participants (replaces existing)
- **Body Examples:**
  
  **Update amount only:**
  ```json
  {
    "amount": 60000
  }
  ```
  
  **Update currency:**
  ```json
  {
    "currency": "USD"
  }
  ```
  
  **Update description:**
  ```json
  {
    "description": "Updated lunch description"
  }
  ```
  
  **Update category:**
  ```json
  {
    "category": "Transportation"
  }
  ```
  
  **Update participants:**
  ```json
  {
    "participant_ids": [1, 2, 3]
  }
  ```
  
  **Update multiple fields:**
  ```json
  {
    "amount": 60000,
    "currency": "USD",
    "description": "Updated lunch description",
    "category": "Food",
    "participant_ids": [1, 2]
  }
  ```
- **Expected:** 200 OK with updated expense
- **Auth Required:** ✅ Bearer Token
- **Note:** 
  - When `amount` or `currency` changes, share amounts are automatically recalculated
  - When `participant_ids` is provided, existing participants are replaced

#### 14. Delete Expense
**Endpoint:** `DELETE /api/expenses/{{expense_id}}`
- **Purpose:** Remove an expense
- **Expected:** 200 OK with success message
- **Auth Required:** ✅ Bearer Token

---

### Phase 5: Diary & Photos

#### 15. Upload Photos (Date-based)
**Endpoint:** `POST /api/diary/{{trip_id}}/2024-07-05/photos`
- **Purpose:** Upload photos for a diary entry (standalone, not linked to expense)
- **Body:** form-data
  - `files`: Select image file(s) (max 10 per user/date, separate from expense-linked photos)
  - `memo`: (optional) "Great day at the beach!"
- **Expected:** 201 Created with photo data
- **Auth Required:** ✅ Bearer Token

#### 16. Upload Photo for Expense ⭐ NEW
**Endpoint:** `POST /api/diary/expenses/{{expense_id}}/photos`
- **Purpose:** Upload ONE photo (receipt, etc.) linked to a specific expense
- **Note:** Only 1 photo allowed per expense_id (uploading again replaces existing photo)
- **Body:** form-data
  - `file`: Select ONE image file (key must be `file`, not `files`)
  - `memo`: (optional) Diary entry memo
- **Expected:** 201 Created with single photo data (not a list)
- **Auth Required:** ✅ Bearer Token
- **Note:** Use `{{expense_id}}` from created expense

#### 17. Get Diary Entry (Date-based)
**Endpoint:** `GET /api/diary/{{trip_id}}/2024-07-05`
- **Purpose:** Get diary entry with photos and memo for a specific date
- **Expected:** 200 OK with diary entry data
- **Auth Required:** ✅ Bearer Token

#### 18. Get Diary Entry for Expense ⭐ NEW
**Endpoint:** `GET /api/diary/expenses/{{expense_id}}`
- **Purpose:** Get diary entry (photos and memo) linked to a specific expense
- **Expected:** 200 OK with diary entry data including photos
- **Auth Required:** ✅ Bearer Token
- **Note:** Returns photos and memo linked to the expense

#### 19. Add/Update Memo (Date-based)
**Endpoint:** `POST /api/diary/{{trip_id}}/2024-07-05/memo`
- **Purpose:** Add or update daily memo (standalone)
- **Body:**
  ```json
  {
    "memo": "Had a wonderful day exploring the city!"
  }
  ```
- **Expected:** 201 Created with diary entry
- **Auth Required:** ✅ Bearer Token

#### 20. Add/Update Memo for Expense ⭐ NEW
**Endpoint:** `POST /api/diary/expenses/{{expense_id}}/memo`
- **Purpose:** Add or update memo linked to a specific expense
- **Body:**
  ```json
  {
    "memo": "Receipt for lunch expense"
  }
  ```
- **Expected:** 201 Created with diary entry
- **Auth Required:** ✅ Bearer Token
- **Note:** Links memo to the expense

#### 21. Get Photo Feed
**Endpoint:** `GET /api/trips/{{trip_id}}/feed?offset=0&limit=10`
- **Purpose:** Get photo timeline (latest first)
- **Expected:** 200 OK with array of photos
- **Auth Required:** ✅ Bearer Token

---

### Phase 6: Calendar & Moods

#### 22. Get Daily Indicators
**Endpoint:** `GET /api/calendar/{{trip_id}}/days`
- **Purpose:** Get calendar view with indicators (expenses, diary, moods)
- **Expected:** 200 OK with array of date indicators
- **Auth Required:** ✅ Bearer Token

#### 23. Get Daily Data
**Endpoint:** `GET /api/calendar/{{trip_id}}/2024-07-05`
- **Purpose:** Get full daily data (expenses, diary, moods)
- **Expected:** 200 OK with complete daily data
- **Auth Required:** ✅ Bearer Token

#### 24. Set Mood
**Endpoint:** `POST /api/calendar/{{trip_id}}/2024-07-05/mood`
- **Purpose:** Set mood emoji for a date
- **Body:**
  ```json
  {
    "date": "2024-07-05",
    "mood_emoji": "😊"
  }
  ```
- **Expected:** 201 Created with mood data
- **Auth Required:** ✅ Bearer Token

---

### Phase 7: Budget Management

#### 25. Set Budget
**Endpoint:** `POST /api/budget/{{trip_id}}`
- **Purpose:** Set personal budget for the trip
- **Body:**
  ```json
  {
    "budget_amount_krw": 1000000
  }
  ```
- **Expected:** 201 Created with budget data
- **Auth Required:** ✅ Bearer Token

#### 26. Get Budget
**Endpoint:** `GET /api/budget/{{trip_id}}`
- **Purpose:** Retrieve current budget
- **Expected:** 200 OK with budget data
- **Auth Required:** ✅ Bearer Token

#### 27. Get Budget Summary
**Endpoint:** `GET /api/budget/{{trip_id}}/summary`
- **Purpose:** Get detailed budget summary with spending
- **Expected:** 200 OK with budget summary (spending, remaining, fill ratio)
- **Auth Required:** ✅ Bearer Token

---

### Phase 8: Settlement

#### 28. Trigger Settlement
**Endpoint:** `POST /api/settlement/{{trip_id}}/trigger`
- **Purpose:** Calculate settlement for finished trip
- **Expected:** 200 OK with settlement result
- **Auth Required:** ✅ Bearer Token
- **Note:** Trip should be finished (end_date in the past)

#### 29. Get Settlement Result
**Endpoint:** `GET /api/settlement/{{trip_id}}/result`
- **Purpose:** Retrieve settlement calculation results
- **Expected:** 200 OK with settlement data (transfers, balances)
- **Auth Required:** ✅ Bearer Token

---

### Phase 9: Exchange Rates (Optional)

#### 30. Get Exchange Rate
**Endpoint:** `GET /api/fx-rates/2024-07-05?currency=USD&trip_id={{trip_id}}`
- **Purpose:** Get exchange rate for a date and currency
- **Expected:** 200 OK with exchange rate data
- **Auth Required:** ✅ Bearer Token

---

### Phase 10: OCR (Optional - Requires OCR Service)

#### 31. Parse Expense Image
**Endpoint:** `POST /api/ocr/parse`
- **Purpose:** Upload receipt/image for OCR expense extraction
- **Body:** form-data with image file
- **Expected:** 200 OK with provisional expense data
- **Auth Required:** ✅ Bearer Token
- **Note:** Requires OCR service to be running

---

## Quick Testing Checklist

### Must Test (Core Functionality)
- [ ] 1. Health Check
- [ ] 2. Sign Up
- [ ] 3. Login
- [ ] 5. Create Trip
- [ ] 11. Create Expense
- [ ] 16. Upload Photo for Expense
- [ ] 20. Add Memo for Expense
- [ ] 25. Set Budget

### Should Test (Important Features)
- [ ] 4. Get Current User
- [ ] 6. List Trips
- [ ] 7. Get Trip Details
- [ ] 12. Get Expenses
- [ ] 17. Get Diary Entry (Date-based)
- [ ] 18. Get Diary Entry for Expense
- [ ] 22. Get Daily Indicators
- [ ] 26. Get Budget

### Nice to Test (Advanced Features)
- [ ] 9. Invite Participant
- [ ] 13. Update Expense
- [ ] 15. Upload Photos (Date-based)
- [ ] 19. Add Memo (Date-based)
- [ ] 24. Set Mood
- [ ] 27. Get Budget Summary
- [ ] 28. Trigger Settlement

---

## Testing Tips

1. **Always login first** - Most endpoints require authentication
2. **Use variables** - The collection auto-saves `trip_id` and `expense_id`
3. **Check responses** - Verify status codes and response structure
4. **Test error cases** - Try invalid data, missing auth, etc.
5. **Use realistic dates** - Make sure dates are within trip date range
6. **Test with multiple users** - Create second user to test participant features
7. **Expense-linked diary** - Use expense_id endpoints to link photos/memos to expenses

## Expense-Linked Diary Testing Flow ⭐

A complete flow for testing expense-linked diary features:

1. **Create Expense** (Step 11)
   - Create an expense and note the `expense_id`
   - Example: `POST /api/expenses/1/2024-07-05`

2. **Upload Photo for Expense** (Step 16)
   - Upload ONE receipt photo linked to the expense
   - Endpoint: `POST /api/diary/expenses/{{expense_id}}/photos`
   - Body: form-data with ONE image file (key: `file`)
   - Note: Only 1 photo allowed per expense_id (uploading again replaces the existing photo)

3. **Add Memo for Expense** (Step 20)
   - Add a memo/note about the expense
   - Endpoint: `POST /api/diary/expenses/{{expense_id}}/memo`
   - Body: `{"memo": "Receipt saved"}`
   - Note: Only 1 memo allowed per expense_id

4. **Get Diary for Expense** (Step 18)
   - View the photo and memo linked to the expense
   - Endpoint: `GET /api/diary/expenses/{{expense_id}}`
   - Should return diary entry with 1 photo and memo

**Important Distinctions:**
- **Expense-based**: 1 photo + 1 memo per expense_id (linked to specific expense)
- **Date-based**: Up to 10 photos + 1 memo per date (standalone diary entry, separate from expenses)
- These are completely separate - date-based entries don't count expense-linked photos

---

## Common Issues

- **401 Unauthorized:** Login again to refresh token
- **404 Not Found:** Check if IDs exist (trip_id, expense_id, etc.)
- **403 Forbidden:** User doesn't have access to the resource
- **422 Validation Error:** Check request body format matches schema

---

## Next Steps

After testing all endpoints:
1. Test error scenarios
2. Test edge cases (empty data, boundary values)
3. Test with multiple users
4. Test concurrent requests
5. Review API documentation at `/docs`

