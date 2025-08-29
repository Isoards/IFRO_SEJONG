import axios from 'axios';

// 환경변수에서 챗봇 IP 가져오기 (기본값: localhost:8008)
const CHATBOT_IP = process.env.REACT_APP_CHATBOT_IP || 'http://localhost:8008';

// 디버깅을 위한 로그
console.log('ChatBot IP:', CHATBOT_IP);
console.log('Environment variable:', process.env.REACT_APP_CHATBOT_IP);

// 챗봇 API 인스턴스 생성 (API 경로 제거)
const chatApi = axios.create({
  baseURL: CHATBOT_IP,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json'
  }
});

// 요청 인터셉터 - 토큰 추가
chatApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 에러 처리
chatApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Chat API Error:', error);
    return Promise.reject(error);
  }
);

// 챗봇 메시지 전송 함수
export const sendChatMessage = async (message: string, context?: any): Promise<string> => {
  try {
    // 간단한 챗봇 API의 /chat 엔드포인트 사용
    const response = await chatApi.post('chat', {
      message: message
    });
    
    if (response.data && response.data.success && response.data.response) {
      return response.data.response;
    } else {
      throw new Error('챗봇 응답이 올바르지 않습니다.');
    }
  } catch (error: any) {
    console.error('Chat message error:', error);
    
    if (error.response?.status === 400) {
      throw new Error('메시지가 비어있습니다.');
    } else if (error.response?.status === 401) {
      throw new Error('인증이 필요합니다. 다시 로그인해주세요.');
    } else if (error.response?.status === 404) {
      throw new Error('챗봇 서비스에 필요한 데이터가 없습니다. 관리자에게 문의해주세요.');
    } else if (error.response?.status === 500) {
      throw new Error('챗봇 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('요청 시간이 초과되었습니다. 네트워크 상태를 확인해주세요.');
    } else if (error.message.includes('Network Error')) {
      throw new Error('챗봇 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.');
    }
    
    throw new Error(`챗봇 응답 오류: ${error.response?.data?.message || error.message}`);
  }
};

// 챗봇 연결 상태 확인 함수
export const checkChatServerStatus = async (): Promise<boolean> => {
  try {
    await chatApi.get('health', { timeout: 5000 });
    return true;
  } catch (error) {
    return false;
  }
};

// 간단한 테스트 함수
export const testChatConnection = async (): Promise<void> => {
  try {
    console.log('Testing chat connection...');
    console.log('Base URL:', chatApi.defaults.baseURL);
    
    const response = await chatApi.get('health');
    console.log('Health check response:', response.data);
  } catch (error) {
    console.error('Connection test failed:', error);
  }
};
