import api from "./axios";
import { 
  Intersection, 
  TrafficInterpretationRequest, 
  TrafficInterpretationResponse,
  ReportData,
  ApiTrafficData,
  TrafficData,
  AIAnalysisResponse
} from "../types/global.types";

export const getIntersectionTrafficData = async (
  intersectionId: number,
  startTime: string,
  endTime: string
): Promise<ApiTrafficData[]> => {
  try {
    const response = await api.get(
      `/traffic/traffic-data/intersection/${intersectionId}`,
      {
        params: { start_time: startTime, end_time: endTime },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching intersection traffic data:', error);
    throw error;
  }
};

export const getLatestIntersectionTrafficData = async (
  intersectionId: number,
  count: number = 10
): Promise<ApiTrafficData[]> => {
  try {
    const response = await api.get(
      `/traffic/traffic-data/intersection/${intersectionId}/latest`,
      {
        params: { count },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching latest intersection traffic data:', error);
    throw error;
  }
};

export const getTrafficIntersections = async (): Promise<Intersection[]> => {
  const response = await api.get("traffic/intersections");
  const data = response.data.map((item: any) => ({
    ...item,
    total_volume: item.total_volume || 0,
  }));
  return data;
};

// 특정 교차로, 특정 시간의 통계(가장 가까운 1시간)를 받아오는 함수
export const getIntersectionTrafficStat = async (intersectionId: number, datetime: string) => {
  const response = await api.get(`traffic/intersections/${intersectionId}/total_volumes`, {
    params: { datetime }
  });
  // 가장 가까운 1개만 반환한다고 가정
  return response.data[0] || null;
};

// 교통 해석 API 호출 함수 - 재시도 로직 포함
export const generateTrafficInterpretation = async (
  requestData: TrafficInterpretationRequest,
  maxRetries: number = 3
): Promise<TrafficInterpretationResponse> => {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await api.post("traffic/generate-interpretation", requestData);
      return response.data;
    } catch (error: any) {
      lastError = error;
      
      // 재시도하지 않을 오류 유형들
      if (error.response?.status === 400 || error.response?.status === 401 || error.response?.status === 403) {
        throw new Error(`API 요청 오류: ${error.response?.data?.message || error.message}`);
      }
      
      // 마지막 시도가 아닌 경우 잠시 대기 후 재시도
      if (attempt < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000); // 지수 백오프, 최대 5초
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
    }
  }
  
  // 모든 재시도 실패 시
  throw new Error(`교통 해석 생성 실패 (${maxRetries}회 시도): ${lastError?.message || '알 수 없는 오류'}`);
};

// 교차로 교통 통계 데이터로부터 해석을 생성하는 편의 함수
export const generateIntersectionTrafficInterpretation = async (
  intersectionId: number,
  datetime: string,
  trafficStat: any // 기존 getIntersectionTrafficStat 반환 타입과 호환
): Promise<TrafficInterpretationResponse> => {
  if (!trafficStat) {
    throw new Error('교통 통계 데이터가 없습니다.');
  }

  const requestData: TrafficInterpretationRequest = {
    intersection_id: intersectionId,
    datetime: datetime,
    traffic_volumes: {
      N: trafficStat.N || 0,
      S: trafficStat.S || 0,
      E: trafficStat.E || 0,
      W: trafficStat.W || 0,
    },
    total_volume: trafficStat.total_volume || 0,
    average_speed: trafficStat.average_speed || 0,
  };

  return generateTrafficInterpretation(requestData);
};

// AI 교통 분석 API 호출 함수
export const generateAITrafficAnalysis = async (
  intersectionId: number,
  timePeriod: string = "24h",
  language: string = "ko"
): Promise<AIAnalysisResponse> => {
  try {
    const response = await api.post(`traffic/intersections/${intersectionId}/ai-analysis`, null, {
      params: { 
        time_period: timePeriod,
        language: language
      },
      timeout: 60000 // 60초 타임아웃
    });
    
    // 응답 데이터 검증
    if (!response.data || !response.data.analysis) {
      throw new Error('AI 분석 응답 데이터가 올바르지 않습니다.');
    }
    
    return response.data;
  } catch (error: any) {
    console.error('AI Analysis API Error:', error);
    
    if (error.response?.status === 404) {
      throw new Error('교차로를 찾을 수 없습니다.');
    } else if (error.response?.status === 400) {
      throw new Error('잘못된 요청입니다. 시간 범위를 확인해주세요.');
    } else if (error.response?.status === 429) {
      throw new Error('AI 분석 서비스 사용량 한도를 초과했습니다. 잠시 후 다시 시도해주세요.');
    } else if (error.response?.status === 500) {
      throw new Error('AI 분석 서비스에 문제가 발생했습니다. API 키 설정을 확인해주세요.');
    } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      throw new Error('AI 분석 요청 시간이 초과되었습니다. 다시 시도해주세요.');
    }
    
    throw new Error(`AI 분석 생성 실패: ${error.response?.data?.message || error.message}`);
  }
}

export const getIntersectionReportData = async (
  intersectionId: number,
  datetime?: string,
  language?: string
): Promise<ReportData> => {
  try {
    const params: any = {};
    if (datetime) params.datetime_str = datetime;
    if (language) params.language = language;
    
    const response = await api.get(
      `/traffic/intersections/${intersectionId}/report-data`,
      { params }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching intersection report data:', error);
    throw error;
  }
};
