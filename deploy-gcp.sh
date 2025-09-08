#!/bin/bash

# GCP 배포 스크립트
set -e

echo "🚀 GCP 배포 시작..."

# 환경 변수 로드 (백엔드 폴더의 .env.prod 사용)
if [ -f django-react-backend-api-ifro/.env.prod ]; then
    source django-react-backend-api-ifro/.env.prod
else
    echo "❌ django-react-backend-api-ifro/.env.prod 파일을 찾을 수 없습니다."
    exit 1
fi

# MYSQL_HOST를 Cloud SQL로 강제 설정
MYSQL_HOST="/cloudsql/$GCP_PROJECT_ID:$GCP_REGION:ifro-mysql-instance"

# GCP 프로젝트 설정
echo "📋 GCP 프로젝트 설정..."
gcloud config set project $GCP_PROJECT_ID

# 필요한 API 활성화
echo "🔧 GCP API 활성화..."
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com

# Cloud SQL 인스턴스 생성 (MySQL)
echo "🗄️ Cloud SQL 인스턴스 생성..."
gcloud sql instances create ifro-mysql-instance \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=$GCP_REGION \
    --root-password=$MYSQL_ROOT_PASSWORD \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=02:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=02

# 데이터베이스 생성
echo "📊 데이터베이스 생성..."
gcloud sql databases create $MYSQL_DATABASE \
    --instance=ifro-mysql-instance

# 사용자 생성
echo "👤 데이터베이스 사용자 생성..."
gcloud sql users create $MYSQL_USER \
    --instance=ifro-mysql-instance \
    --password=$MYSQL_PASSWORD

# Cloud Run 서비스 배포
echo "🐳 Docker 이미지 빌드 및 배포..."

# 백엔드 배포
echo "🔧 백엔드 배포..."
cd django-react-backend-api-ifro
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/ifro-backend

gcloud run deploy ifro-backend \
    --image gcr.io/$GCP_PROJECT_ID/ifro-backend \
    --platform managed \
    --region $GCP_REGION \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars="DJANGO_SETTINGS_MODULE=dashboard.settings,DJANGO_DEBUG=False,DJANGO_ALLOWED_HOSTS=*,MYSQL_DATABASE=$MYSQL_DATABASE,MYSQL_USER=$MYSQL_USER,MYSQL_PASSWORD=$MYSQL_PASSWORD,MYSQL_HOST=/cloudsql/$GCP_PROJECT_ID:$GCP_REGION:ifro-mysql-instance,MYSQL_PORT=3306,DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY,JWT_SECRET_KEY=$JWT_SECRET_KEY,DJANGO_ENCRYPTION_PASSWORD=$DJANGO_ENCRYPTION_PASSWORD,GEMINI_API_KEY=$GEMINI_API_KEY,CHATBOT_URL=$CHATBOT_URL" \
    --add-cloudsql-instances $GCP_PROJECT_ID:$GCP_REGION:ifro-mysql-instance

cd ..

# 프론트엔드 배포
echo "🎨 프론트엔드 배포..."
cd django-react-frontend-ifro
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/ifro-frontend

gcloud run deploy ifro-frontend \
    --image gcr.io/$GCP_PROJECT_ID/ifro-frontend \
    --platform managed \
    --region $GCP_REGION \
    --allow-unauthenticated \
    --port 80

cd ..

echo "✅ 배포 완료!"
echo "🌐 프론트엔드 URL: $(gcloud run services describe ifro-frontend --region=$GCP_REGION --format='value(status.url)')"
echo "🔧 백엔드 URL: $(gcloud run services describe ifro-backend --region=$GCP_REGION --format='value(status.url)')" 