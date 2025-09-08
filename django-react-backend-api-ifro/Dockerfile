FROM --platform=linux/amd64 python:3.10-slim

# 한글 지원을 위한 로케일 설정
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LC_CTYPE=ko_KR.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y \
  gcc \
  default-libmysqlclient-dev \
  build-essential \
  libssl-dev \
  pkg-config \
  default-mysql-client \
  locales \
  && rm -rf /var/lib/apt/lists/*

# 한글 로케일 생성
RUN locale-gen ko_KR.UTF-8

COPY python_encrypter-0.1.0-py3-none-any.whl ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 프로덕션용 WSGI 서버 설치
RUN pip install gunicorn

# 환경 변수 설정
ENV DJANGO_SETTINGS_MODULE=dashboard.settings
ENV PYTHONPATH=/app/src

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# 프로덕션 실행 명령
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "dashboard.wsgi:application"]