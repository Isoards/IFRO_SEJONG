FROM python:3.10-slim

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

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]