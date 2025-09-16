# GPU 설정 가이드

## 🎯 GPU 지원을 위한 Docker 설정

### 1. NVIDIA Docker 설정 확인

#### Windows (WSL2 + Docker Desktop)
```bash
# NVIDIA Container Toolkit 설치 확인
nvidia-smi

# Docker에서 GPU 사용 가능한지 확인
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### Linux
```bash
# NVIDIA Container Toolkit 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Docker Compose 사용법

#### GPU 지원 버전 사용
```bash
# GPU 지원으로 AI 서비스 실행
docker-compose -f docker-compose.gpu.yml up -d

# 또는 기본 설정에서 GPU 사용 (docker-compose.yml에 GPU 설정 포함됨)
docker-compose up -d ollama chatbot
```

#### GPU 없이 CPU만 사용
```bash
# CPU 전용으로 실행 (기본 설정)
docker-compose up -d ollama chatbot
```

### 3. GPU 사용 확인

#### Ollama 서비스에서 GPU 사용 확인
```bash
# 컨테이너 내부에서 GPU 확인
docker exec -it ollama nvidia-smi

# 또는 Ollama API로 확인
curl http://localhost:11434/api/ps
```

#### 모델 실행 시 GPU 사용 확인
```bash
# 모델 실행 시 GPU 메모리 사용량 확인
docker exec -it ollama ollama run llama3.1:8b-instruct-q4_K_M "안녕하세요"
```

### 4. 성능 비교

| 설정 | 메모리 사용량 | 추론 속도 | 권장 환경 |
|------|---------------|-----------|-----------|
| **CPU 전용** | ~4-6GB RAM | 느림 | 개발/테스트 |
| **GPU 지원** | ~2-4GB VRAM | 빠름 | 프로덕션 |

### 5. 문제 해결

#### GPU 인식 안됨
```bash
# Docker Desktop에서 GPU 지원 활성화 확인
# Settings > Resources > WSL Integration > Enable integration with additional distros

# NVIDIA 드라이버 버전 확인
nvidia-smi
```

#### 메모리 부족
```bash
# GPU 메모리 사용량 확인
nvidia-smi

# 모델 크기 조정 (더 작은 모델 사용)
ollama pull llama3.1:1b-instruct-q4_K_M
```

#### 컨테이너 시작 실패
```bash
# Docker 로그 확인
docker logs ollama

# GPU 런타임 확인
docker info | grep -i runtime
```

### 6. 환경별 권장 설정

#### 개발 환경 (GPU 없음)
```bash
docker-compose up -d db backend frontend
# AI 서비스는 필요시에만 실행
```

#### 프로덕션 환경 (GPU 있음)
```bash
docker-compose -f docker-compose.gpu.yml up -d
```

#### 하이브리드 환경
```bash
# 웹 서비스는 로컬, AI 서비스는 GPU 서버에서
docker-compose up -d db backend frontend
# 별도 GPU 서버에서 AI 서비스 실행
```
