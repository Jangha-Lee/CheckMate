# MySQL 연결 오류 해결 방법

## 방법 1: Docker로 MySQL만 실행 (권장)

### 0단계: Docker Desktop 시작 (필수!)
**중요**: Docker Desktop이 실행 중이어야 합니다.

1. Windows 시작 메뉴에서 **Docker Desktop** 검색 후 실행
2. Docker Desktop이 완전히 시작될 때까지 대기 (시스템 트레이 아이콘 확인)
3. 다음 명령어로 Docker가 실행 중인지 확인:
```powershell
docker ps
```
오류가 없으면 Docker가 정상적으로 실행 중입니다.

### 1단계: MySQL 컨테이너 시작
```powershell
cd backend
docker-compose -f docker-compose.mysql-only.yml up -d
```

**오류 발생 시**:
- `unable to get image` 또는 `dockerDesktopLinuxEngine` 오류 → Docker Desktop을 시작하세요
- `version is obsolete` 경고 → 무시해도 됩니다 (Docker Compose 최신 버전에서 version 필드가 선택사항)

### 2단계: MySQL이 실행 중인지 확인
```powershell
docker ps
```
`checkmate-mysql-local` 컨테이너가 실행 중이어야 합니다.

### 3단계: .env 파일 생성
`backend` 폴더에 `.env` 파일을 만들고 다음 내용을 추가:

```env
# Database (for local MySQL in Docker)
DATABASE_URL=mysql+pymysql://checkmate_user:checkmate_password@localhost:3306/checkmate_db
DB_ECHO=false

# Application Settings
APP_NAME=Checkmate
DEBUG=true

# JWT
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=app/static

# OCR (optional)
OCR_SERVICE_URL=http://localhost:8001
OCR_API_KEY=K81156818088957
OCR_PROVIDER=ocrspace

# Exchange Rate (optional)
FX_API_KEY=
FX_BASE_CURRENCY=KRW
```

### 4단계: 데이터베이스 초기화
```powershell
python -m app.db.init_db
```

---

## 방법 2: 로컬에 MySQL 설치 (Docker 없이)

Docker Desktop을 사용하지 않으려면 로컬에 MySQL을 직접 설치할 수 있습니다.

### 1단계: MySQL 설치
1. [MySQL 공식 사이트](https://dev.mysql.com/downloads/mysql/)에서 MySQL 8.0 다운로드
2. MySQL 설치 및 설정 마법사 실행
3. Root 비밀번호 설정
4. MySQL 서비스가 자동으로 시작되도록 설정

### 1-1단계: MySQL 서비스 확인
```powershell
Get-Service | Where-Object {$_.Name -like "*mysql*"}
```
서비스가 실행 중이어야 합니다. 실행 중이 아니면:
```powershell
# 서비스 이름 확인 후 (예: MySQL80)
Start-Service MySQL80
```

### 2단계: 데이터베이스 및 사용자 생성
MySQL에 접속하여:
```sql
CREATE DATABASE checkmate_db;
CREATE USER 'checkmate_user'@'localhost' IDENTIFIED BY 'checkmate_password';
GRANT ALL PRIVILEGES ON checkmate_db.* TO 'checkmate_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3단계: .env 파일 생성
방법 1의 3단계와 동일합니다.

---

## 방법 3: 전체 Docker Compose 사용

모든 서비스를 Docker로 실행:
```powershell
cd backend
docker-compose up -d
```

이 경우 `.env` 파일의 `DATABASE_URL`은:
```env
DATABASE_URL=mysql+pymysql://checkmate_user:checkmate_password@mysql:3306/checkmate_db
```
(호스트가 `mysql`이어야 함 - Docker 네트워크 내에서)

---

## 문제 해결

### MySQL이 실행 중인지 확인
```powershell
# Docker로 실행한 경우
docker ps | findstr mysql

# 로컬 MySQL인 경우
Get-Service | Where-Object {$_.Name -like "*mysql*"}
```

### MySQL 연결 테스트
```powershell
# Docker MySQL인 경우
docker exec -it checkmate-mysql-local mysql -u checkmate_user -pcheckmate_password checkmate_db

# 로컬 MySQL인 경우
mysql -u checkmate_user -pcheckmate_password checkmate_db
```

### 포트 확인
```powershell
netstat -an | findstr 3306
```
포트 3306이 LISTENING 상태여야 합니다.

