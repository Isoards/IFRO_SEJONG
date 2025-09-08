# GCP 배포 가이드

## 사전 준비사항

1. **Google Cloud SDK 설치**
   ```bash
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **GCP 계정 설정**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **프로젝트 생성**
   ```bash
   gcloud projects create [PROJECT_ID] --name="IFRO_SEJONG"
   gcloud config set project [PROJECT_ID]
   ```

## 배포 단계

### 1. 환경 변수 설정

`env.prod.example` 파일을 복사하여 `.env.prod` 파일을 생성하고 실제 값으로 수정:

```bash
cp env.prod.example .env.prod
```

다음 값들을 실제 값으로 변경:
- `your_secure_password_here`: 안전한 데이터베이스 비밀번호
- `your_django_secret_key_here`: Django 시크릿 키
- `your_jwt_secret_key_here`: JWT 시크릿 키
- `your_encryption_password_here`: 암호화 비밀번호
- `your_gemini_api_key_here`: Gemini API 키
- `your_project_id_here`: GCP 프로젝트 ID

### 2. 배포 실행

**방법 1: 간단한 배포 (권장)**
```bash
chmod +x deploy-simple.sh
./deploy-simple.sh
```

**방법 2: 기본 배포**
```bash
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

**방법 3: Linux 플랫폼 명시적 지정**
```bash
chmod +x deploy-gcp-linux.sh
./deploy-gcp-linux.sh
```

### 3. 로컬 빌드 테스트 (선택사항)

배포 전에 로컬에서 Linux 플랫폼 빌드가 정상적으로 되는지 테스트:

```bash
chmod +x build-local.sh
./build-local.sh
```

또는 수동으로 단계별 실행:

```bash
# 1. GCP API 활성화
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com

# 2. Cloud SQL 인스턴스 생성
gcloud sql instances create ifro-mysql-instance \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=asia-northeast3 \
    --root-password=[ROOT_PASSWORD] \
    --storage-type=SSD \
    --storage-size=10GB

# 3. 데이터베이스 및 사용자 생성
gcloud sql databases create traffic --instance=ifro-mysql-instance
gcloud sql users create root --instance=ifro-mysql-instance --password=[USER_PASSWORD]

# 4. Docker 이미지 빌드 및 배포
cd django-react-backend-api-ifro
gcloud builds submit --tag gcr.io/[PROJECT_ID]/ifro-backend
gcloud run deploy ifro-backend --image gcr.io/[PROJECT_ID]/ifro-backend --platform managed --region asia-northeast3 --allow-unauthenticated --port 8000

cd ../django-react-frontend-ifro
gcloud builds submit --tag gcr.io/[PROJECT_ID]/ifro-frontend
gcloud run deploy ifro-frontend --image gcr.io/[PROJECT_ID]/ifro-frontend --platform managed --region asia-northeast3 --allow-unauthenticated --port 80

# 또는 Cloud Build 설정 파일 사용
gcloud builds submit --config cloudbuild-linux.yaml
```

## 서비스 URL 확인

배포 완료 후 다음 명령어로 서비스 URL을 확인할 수 있습니다:

```bash
# 프론트엔드 URL
gcloud run services describe ifro-frontend --region=asia-northeast3 --format='value(status.url)'

# 백엔드 URL
gcloud run services describe ifro-backend --region=asia-northeast3 --format='value(status.url)'
```

## 비용 최적화

1. **Cloud SQL 인스턴스**: `db-f1-micro` (가장 작은 인스턴스)
2. **Cloud Run**: 요청이 있을 때만 실행되어 비용 절약
3. **리전**: `asia-northeast3` (서울) - 한국에서 가장 빠른 속도

## 모니터링

```bash
# 로그 확인
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# 서비스 상태 확인
gcloud run services list --region=asia-northeast3
```

## 문제 해결

### 일반적인 문제들:

1. **권한 오류**: IAM에서 적절한 권한 부여
2. **데이터베이스 연결 오류**: Cloud SQL 인스턴스 상태 확인
3. **빌드 실패**: Dockerfile 문법 오류 확인
4. **플랫폼 호환성**: M1 Mac에서 빌드 시 Linux 플랫폼 지정 필요

### 빌드 실패 해결 방법:

1. **로컬 빌드 테스트**:
   ```bash
   ./build-local.sh
   ```

2. **캐시 클리어**:
   ```bash
   docker system prune -a
   ```

3. **단계별 배포**:
   ```bash
   ./deploy-simple.sh
   ```

4. **Craco 오류 해결**:
   - `@craco/craco`가 dependencies에 있는지 확인
   - Dockerfile에서 `npm ci --include=dev` 사용

5. **Cloud Run 포트 오류 해결**:
   - nginx 설정에서 `$PORT` 환경변수 사용
   - 시작 스크립트에서 포트 동적 설정
   - Linux 플랫폼 명시적 지정

### 로그 확인:
```bash
gcloud run services logs read ifro-backend --region=asia-northeast3
gcloud run services logs read ifro-frontend --region=asia-northeast3
```

## 보안 고려사항

1. **환경 변수**: 민감한 정보는 Secret Manager 사용 권장
2. **HTTPS**: Cloud Run은 기본적으로 HTTPS 제공
3. **방화벽**: Cloud SQL은 기본적으로 비공개 네트워크

## 확장성

- **수평 확장**: Cloud Run은 자동 스케일링 지원
- **데이터베이스**: 필요시 더 큰 Cloud SQL 인스턴스로 업그레이드
- **CDN**: Cloud CDN 추가로 정적 파일 서빙 최적화 