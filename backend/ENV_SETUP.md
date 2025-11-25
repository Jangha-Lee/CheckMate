# Environment Variables Setup

This document describes all environment variables needed for the Checkmate backend application.

## Required Environment Variables

### Database Configuration
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/checkmate
```

### JWT Authentication
```env
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
```

### Exchange Rate API
```env
FX_API_KEY=your-exchange-rate-api-key
FX_BASE_CURRENCY=KRW  # Base currency for normalization (e.g., KRW, USD, EUR, JPY, CNY, AUD, GBP, etc.)
```

**Base Currency Configuration:**
- **Purpose**: All expenses are normalized to the base currency for calculations, settlements, and reporting
- **Default**: `KRW` (if not specified)
- **Supported**: Any valid ISO 4217 currency code supported by ExchangeRate-API
- **Example**: Set `FX_BASE_CURRENCY=USD` to use US Dollar as base currency

**Note**: Once set, changing the base currency may cause inconsistencies with existing data. It's recommended to set it once before production.

### OpenAI API (for Expense Category Classification)
```env
# OpenAI API Key - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Custom OpenAI API endpoint (default: https://api.openai.com/v1/chat/completions)
# OPENAI_API_URL=https://api.openai.com/v1/chat/completions

# Optional: OpenAI model to use (default: gpt-3.5-turbo)
# Options: gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview, etc.
# OPENAI_MODEL=gpt-3.5-turbo
```

### OCR Configuration

#### OCR Provider Selection
```env
# Options: "ocrspace", "google_vision", "naver_clova", "openai_vision", "tesseract"
# Recommended: "openai_vision" for best accuracy (uses GPT-4 Vision to extract structured payment records)
OCR_PROVIDER=openai_vision
```

#### OCR.space (Default)
```env
OCR_API_KEY=K81156818088957
```

#### Naver Clova OCR
```env
# Naver Clova OCR API Gateway URL
NAVER_CLOVA_API_URL=https://your-gateway-id.apigw.ntruss.com/custom/v1/your-service-id/your-api-key/general

# Naver Clova OCR Secret Key (X-OCR-SECRET)
NAVER_CLOVA_SECRET_KEY=your-secret-key-here

# Optional: Template IDs for template-based OCR (comma-separated)
# NAVER_CLOVA_TEMPLATE_IDS=123,456

# Optional: Use auto integration mode (JSON with base64) instead of manual (multipart/form-data)
# NAVER_CLOVA_AUTO_INTEGRATION=true
```

## Example .env File

```env
# Application
APP_NAME=Checkmate
DEBUG=False

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/checkmate
DB_ECHO=False

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Exchange Rate API
FX_API_KEY=your-exchange-rate-api-key
FX_BASE_CURRENCY=KRW

# OpenAI API (for Expense Category Classification)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# OCR
OCR_PROVIDER=naver_clova
NAVER_CLOVA_API_URL=https://your-gateway-id.apigw.ntruss.com/custom/v1/your-service-id/your-api-key/general
NAVER_CLOVA_SECRET_KEY=your-secret-key-here
NAVER_CLOVA_AUTO_INTEGRATION=true
```

## Notes

- **OpenAI API Key**: Required for automatic expense category classification. If not provided, expenses will default to "other" category.
- **FX API Key**: Required for currency conversion. Get from [ExchangeRate-API](https://www.exchangerate-api.com/).
- **Naver Clova OCR**: Optional, but recommended for better OCR accuracy, especially for Korean text and structured receipts.
- All optional variables have default values and can be omitted if not needed.

