# Build stage
FROM --platform=linux/amd64 node:18-alpine AS build

WORKDIR /app

# 패키지 파일 복사 및 설치 (devDependencies 포함)
COPY package*.json ./
RUN npm ci --include=dev

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# Production stage
FROM --platform=linux/amd64 nginx:alpine

# nginx 설정 복사 (conf.d로)
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]