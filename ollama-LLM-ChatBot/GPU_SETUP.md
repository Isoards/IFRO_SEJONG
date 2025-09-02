# GPU 설정 가이드

이 문서는 CUDA GPU를 사용하여 챗봇 시스템을 실행하는 방법을 설명합니다.

## 🚀 주요 기능

- **CUDA GPU 지원**: NVIDIA GPU를 사용한 가속 처리
- **CPU 폴백**: GPU가 없거나 사용할 수 없는 경우 자동으로 CPU 사용
- **지연 로딩 제거**: 모든 모델을 즉시 로드하여 빠른 응답
- **메모리 최적화**: GPU/CPU 메모리 효율적 사용

## 📋 시스템 요구사항

### GPU 사용 시
- NVIDIA GPU (CUDA 지원)
- CUDA 11.8 이상
- cuDNN 8.0 이상
- 최소 8GB GPU 메모리 (권장 16GB+)
- 최소 16GB 시스템 메모리

### CPU 사용 시
- 최소 8GB 시스템 메모리 (권장 16GB+)
- 멀티코어 CPU (권장 4코어 이상)

## 🔧 설치 및 설정

### 1. CUDA 드라이버 설치

#### Windows
```bash
# NVIDIA 드라이버 다운로드 및 설치
# https://www.nvidia.com/Download/index.aspx
```

#### Linux (Ubuntu)
```bash
# CUDA Toolkit 설치
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt-get install cuda-11-8
```

### 2. Docker GPU 지원 설정

#### NVIDIA Container Toolkit 설치
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### Windows
```bash
# Docker Desktop에서 WSL 2 사용 시
# NVIDIA GPU Support 활성화
```

### 3. 프로젝트 실행

#### Docker Compose로 실행 (권장)
```bash
# GPU 지원으로 실행
docker-compose up -d

# GPU 상태 확인
docker exec ifro-chatbot nvidia-smi
```

#### 로컬 실행
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python run_server.py
```

## 🔍 GPU 상태 확인

### Docker 컨테이너 내부에서
```bash
# GPU 정보 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

### 로컬 환경에서
```bash
# CUDA 버전 확인
nvcc --version

# GPU 드라이버 확인
nvidia-smi
```

## ⚙️ 환경 변수 설정

### GPU 관련 환경 변수
```bash
# GPU 설정
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility

# 모델 설정
MODEL_TYPE=local
MODEL_NAME=beomi/KoAlpaca-Polyglot-5.8B
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask

# 메모리 설정
MAX_MODEL_MEMORY_GB=8.0
MEMORY_WARNING_THRESHOLD=75.0
MEMORY_CRITICAL_THRESHOLD=85.0
```

## 🐛 문제 해결

### GPU가 인식되지 않는 경우
1. CUDA 드라이버 설치 확인
```bash
nvidia-smi
```

2. Docker GPU 지원 확인
```bash
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

3. PyTorch CUDA 설치 확인
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

### 메모리 부족 오류
1. GPU 메모리 확인
```bash
nvidia-smi
```

2. 모델 메모리 설정 조정
```bash
# 환경 변수에서 메모리 제한 조정
MAX_MODEL_MEMORY_GB=4.0
```

### 성능 최적화
1. GPU 메모리 최적화
```python
# float16 사용으로 메모리 절약
torch_dtype=torch.float16
```

2. 배치 크기 조정
```python
# 작은 배치 크기로 메모리 사용량 감소
batch_size=1
```

## 📊 성능 비교

| 설정 | 응답 시간 | 메모리 사용량 | 정확도 |
|------|-----------|---------------|--------|
| GPU (float16) | ~2초 | 8GB | 높음 |
| GPU (float32) | ~3초 | 16GB | 매우 높음 |
| CPU | ~10초 | 4GB | 높음 |

## 🔄 CPU 폴백

GPU를 사용할 수 없는 경우 자동으로 CPU로 전환됩니다:

1. **CUDA 드라이버 없음**: 자동 CPU 사용
2. **GPU 메모리 부족**: CPU로 폴백
3. **GPU 오류**: CPU로 폴백

로그에서 확인할 수 있는 메시지:
```
[WARNING] CUDA를 사용할 수 없습니다. CPU를 사용합니다.
[INFO] CPU 사용: torch.device('cpu')
```

## 📝 로그 확인

### GPU 사용 시 로그
```
[GPU] CUDA 사용 가능: 1개 GPU
[GPU] 현재 GPU: NVIDIA GeForce RTX 3080
[GPU] GPU 메모리: 10.0GB
[SUCCESS] CUDA GPU 사용: cuda
```

### CPU 사용 시 로그
```
[WARNING] CUDA를 사용할 수 없습니다. CPU를 사용합니다.
[INFO] CPU 사용: torch.device('cpu')
```

## 🚀 최적화 팁

1. **GPU 메모리 관리**
   - float16 사용으로 메모리 절약
   - 불필요한 모델 언로드
   - 배치 크기 최적화

2. **CPU 최적화**
   - 멀티스레딩 활용
   - 메모리 매핑 사용
   - 캐싱 활성화

3. **네트워크 최적화**
   - 로컬 모델 사용
   - CDN 활용
   - 압축 전송

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. 시스템 요구사항 충족 여부
2. CUDA 드라이버 설치 상태
3. Docker GPU 지원 설정
4. 로그 파일 확인

로그 파일 위치: `./logs/server.log`
