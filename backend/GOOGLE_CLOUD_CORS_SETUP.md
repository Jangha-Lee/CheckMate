# Google Cloud Load Balancer CORS 설정 가이드

Google Cloud 부하 분산기(Load Balancer)에서 프론트엔드 URL 확인 및 CORS 설정 방법입니다.

---

## 1. Google Cloud Console에서 확인하기

### 방법 1: Load Balancer 페이지에서 확인

1. **Google Cloud Console** 접속: https://console.cloud.google.com/
2. 네비게이션 메뉴 → **네트워킹(Networking)** → **부하 분산(Load balancing)**
3. 로드 밸런서 선택
4. **프론트엔드 구성(Frontend configuration)** 탭 클릭
5. 다음 정보 확인:
   - **IP 주소**: 프론트엔드 IP (예: `34.123.45.67`)
   - **포트**: 보통 `80` (HTTP) 또는 `443` (HTTPS)
   - **프로토콜**: HTTP 또는 HTTPS

### 방법 2: 도메인 확인

만약 도메인을 연결했다면:
1. **네트워킹** → **부하 분산** → 로드 밸런서 선택
2. **프론트엔드 구성** 탭에서 도메인 이름 확인
   - 예: `checkmate.com`, `www.checkmate.com`
   - 또는 `api.checkmate.com` (API용)

---

## 2. gcloud CLI로 확인하기

### Load Balancer 목록 확인

```bash
gcloud compute forwarding-rules list
```

**출력 예시:**
```
NAME                      REGION        IP_ADDRESS     IP_PROTOCOL  TARGET
checkmate-lb-frontend     us-central1   34.123.45.67   TCP          checkmate-backend-service
```

### 특정 Load Balancer 상세 정보 확인

```bash
gcloud compute forwarding-rules describe checkmate-lb-frontend \
    --region=us-central1
```

**출력 예시:**
```yaml
IPAddress: 34.123.45.67
IPProtocol: TCP
loadBalancingScheme: EXTERNAL
name: checkmate-lb-frontend
portRange: 80-80  # 또는 443-443
region: us-central1
target: projects/PROJECT_ID/regions/us-central1/targetPools/checkmate-backend-service
```

### HTTP(S) Load Balancer 상세 정보 확인

HTTP(S) Load Balancer의 경우:

```bash
# URL Map 확인
gcloud compute url-maps list

# 특정 URL Map 상세
gcloud compute url-maps describe checkmate-url-map

# Target HTTP(S) Proxy 확인
gcloud compute target-https-proxies list
gcloud compute target-http-proxies list

# Frontend Service 확인
gcloud compute backend-services list
```

---

## 3. 프론트엔드 URL 확인 방법

### 시나리오 A: IP 주소만 있는 경우

**예시:**
```
IP: 34.123.45.67
포트: 443 (HTTPS)
프로토콜: HTTPS
```

**프론트엔드 URL:**
```
https://34.123.45.67
```

**CORS 설정:**
```env
CORS_ORIGINS=https://34.123.45.67
```

### 시나리오 B: 도메인이 연결된 경우

**예시:**
```
도메인: checkmate.com
포트: 443 (HTTPS)
프로토콜: HTTPS
```

**프론트엔드 URL:**
```
https://checkmate.com
https://www.checkmate.com  # www 서브도메인도 있다면
```

**CORS 설정:**
```env
CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
```

### 시나리오 C: 서브도메인 분리 (프론트엔드/백엔드)

**예시:**
```
프론트엔드: https://checkmate.com
백엔드 API: https://api.checkmate.com
```

**CORS 설정 (백엔드 .env):**
```env
CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
```

---

## 4. 백엔드 API URL 확인

### API를 위한 별도 Load Balancer가 있는 경우

1. **네트워킹** → **부하 분산** → API용 로드 밸런서 선택
2. **프론트엔드 구성**에서 IP/도메인 확인
   - 예: `api.checkmate.com` 또는 `34.123.45.68`

### 같은 Load Balancer에 Path 기반 라우팅이 있는 경우

- **프론트엔드**: `https://checkmate.com`
- **백엔드 API**: `https://checkmate.com/api`
- **CORS 설정**: 프론트엔드 도메인만 필요
  ```env
  CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
  ```

---

## 5. CORS 설정 적용 방법

### Step 1: 프론트엔드 URL 확인

위의 방법으로 프론트엔드 URL을 확인합니다.

### Step 2: .env 파일에 추가

백엔드 서버의 `.env` 파일에 추가:

```env
# Google Cloud 프로덕션 환경
CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com

# 또는 IP 주소를 사용하는 경우
# CORS_ORIGINS=https://34.123.45.67

# 개발 환경도 포함하려면
# CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://checkmate.com,https://www.checkmate.com
```

### Step 3: Google Cloud 환경 변수로 설정 (권장)

Cloud Run, App Engine, GKE 등을 사용하는 경우:

**Cloud Run:**
```bash
gcloud run services update checkmate-backend \
    --set-env-vars CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com \
    --region=us-central1
```

**또는 환경 변수 파일 사용:**
```bash
echo "CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com" > .env.prod
gcloud run services update checkmate-backend \
    --env-vars-file=.env.prod \
    --region=us-central1
```

**App Engine (app.yaml):**
```yaml
env_variables:
  CORS_ORIGINS: 'https://checkmate.com,https://www.checkmate.com'
```

**GKE (ConfigMap):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: checkmate-config
data:
  CORS_ORIGINS: "https://checkmate.com,https://www.checkmate.com"
```

### Step 4: 백엔드 서비스 재시작

환경 변수를 변경한 후 백엔드 서비스를 재시작:

**Cloud Run:**
```bash
gcloud run services update checkmate-backend --region=us-central1
```

**App Engine:**
```bash
gcloud app deploy
```

**GKE:**
```bash
kubectl rollout restart deployment/checkmate-backend
```

---

## 6. 확인 및 테스트

### CORS 헤더 확인

프론트엔드에서 API 호출 시 브라우저 개발자 도구의 Network 탭에서 확인:

```
Access-Control-Allow-Origin: https://checkmate.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

### 테스트 명령어

```bash
# OPTIONS 요청 테스트 (Preflight)
curl -X OPTIONS https://api.checkmate.com/api/trips \
    -H "Origin: https://checkmate.com" \
    -H "Access-Control-Request-Method: GET" \
    -v

# 실제 요청 테스트
curl -X GET https://api.checkmate.com/api/trips \
    -H "Origin: https://checkmate.com" \
    -v
```

---

## 7. 일반적인 설정 예시

### 예시 1: 단일 도메인

**Load Balancer 설정:**
- 도메인: `checkmate.com`
- 프로토콜: HTTPS (포트 443)

**CORS 설정:**
```env
CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
```

### 예시 2: 서브도메인 분리

**Load Balancer 설정:**
- 프론트엔드: `checkmate.com`
- 백엔드 API: `api.checkmate.com`

**CORS 설정 (백엔드 .env):**
```env
CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
```

### 예시 3: 개발/프로덕션 모두 지원

**CORS 설정:**
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://checkmate.com,https://www.checkmate.com
```

---

## 8. 문제 해결

### CORS 오류 발생 시

**오류 메시지:**
```
Access to fetch at 'https://api.checkmate.com/api/...' from origin 'https://checkmate.com' 
has been blocked by CORS policy
```

**확인 사항:**

1. ✅ 프론트엔드 URL이 `CORS_ORIGINS`에 정확히 포함되어 있는지 확인
   - 프로토콜 일치 (`https://` vs `http://`)
   - 도메인 일치 (서브도메인 포함 여부 확인)
   - 포트 번호 (포트가 있는 경우)

2. ✅ 환경 변수가 제대로 적용되었는지 확인
   ```bash
   # Cloud Run
   gcloud run services describe checkmate-backend --region=us-central1
   
   # GKE
   kubectl get configmap checkmate-config -o yaml
   ```

3. ✅ 백엔드 서비스가 재시작되었는지 확인

4. ✅ Load Balancer가 백엔드 서비스로 올바르게 라우팅되는지 확인

### 디버깅 명령어

```bash
# 환경 변수 확인 (Cloud Run)
gcloud run services describe checkmate-backend \
    --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env)"

# 환경 변수 확인 (GKE)
kubectl exec -it deployment/checkmate-backend -- env | grep CORS

# 로그 확인
gcloud run services logs read checkmate-backend --region=us-central1
```

---

## 9. 보안 권장사항

### 프로덕션 환경

1. **특정 도메인만 허용**: 와일드카드(`*`) 사용 금지
   ```env
   # ✅ 좋은 예
   CORS_ORIGINS=https://checkmate.com,https://www.checkmate.com
   
   # ❌ 나쁜 예 (보안 취약)
   CORS_ORIGINS=*
   ```

2. **HTTPS만 허용**: 프로덕션에서는 HTTP 제거
   ```env
   # ✅ 좋은 예
   CORS_ORIGINS=https://checkmate.com
   
   # ❌ 나쁜 예
   CORS_ORIGINS=http://checkmate.com,https://checkmate.com
   ```

3. **개발 URL 제거**: 프로덕션에서는 localhost 제거

---

## 10. 추가 리소스

- [Google Cloud Load Balancing 문서](https://cloud.google.com/load-balancing/docs)
- [FastAPI CORS 설정](https://fastapi.tiangolo.com/tutorial/cors/)
- [CORS 정책 이해하기](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

---

**참고:** Load Balancer 설정이 변경되면 위의 명령어로 최신 정보를 확인하세요.

