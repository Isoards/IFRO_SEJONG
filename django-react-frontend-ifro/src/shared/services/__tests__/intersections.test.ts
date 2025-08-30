import { 
  generateTrafficInterpretation, 
  generateIntersectionTrafficInterpretation 
} from '../intersections';
import { 
  TrafficInterpretationRequest, 
  TrafficInterpretationResponse 
} from '../../types/global.types';

// Mock the axios module
jest.mock('../axios', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

// Import the mocked api after mocking
import api from '../axios';
const mockedApi = api as jest.Mocked<typeof api>;

describe('Traffic Interpretation API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('generateTrafficInterpretation', () => {
    const mockRequest: TrafficInterpretationRequest = {
      intersection_id: 1,
      datetime: '2024-01-15T10:00:00Z',
      traffic_volumes: {
        NS: 150,
        SN: 120,
        EW: 200,
        WE: 180
      },
      total_volume: 650,
      average_speed: 45
    };

    const mockResponse: TrafficInterpretationResponse = {
      interpretation: '동서 방향의 교통량이 가장 많으며, 전반적으로 혼잡한 상태입니다.',
      congestion_level: 'high',
      peak_direction: 'EW',
      analysis_summary: {
        busiest_direction: '동서 방향',
        traffic_condition: '혼잡',
        speed_assessment: '보통'
      }
    };

    it('should successfully generate traffic interpretation', async () => {
      mockedApi.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await generateTrafficInterpretation(mockRequest);

      expect(mockedApi.post).toHaveBeenCalledWith(
        'traffic/generate-interpretation/',
        mockRequest
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors and throw meaningful error messages', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { message: 'Invalid request data' }
        }
      };
      mockedApi.post.mockRejectedValueOnce(errorResponse);

      await expect(generateTrafficInterpretation(mockRequest))
        .rejects
        .toThrow('API 요청 오류: Invalid request data');
    });

    it('should handle server errors', async () => {
      const serverError = {
        response: { status: 500 },
        message: 'Internal Server Error'
      };
      
      mockedApi.post.mockRejectedValueOnce(serverError);

      await expect(generateTrafficInterpretation(mockRequest, 1))
        .rejects
        .toThrow('교통 해석 생성 실패');

      expect(mockedApi.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('generateIntersectionTrafficInterpretation', () => {
    const mockTrafficStat = {
      NS: 150,
      SN: 120,
      EW: 200,
      WE: 180,
      total_volume: 650,
      average_speed: 45
    };

    const mockResponse: TrafficInterpretationResponse = {
      interpretation: '동서 방향의 교통량이 가장 많으며, 전반적으로 혼잡한 상태입니다.',
      congestion_level: 'high',
      peak_direction: 'EW',
      analysis_summary: {
        busiest_direction: '동서 방향',
        traffic_condition: '혼잡',
        speed_assessment: '보통'
      }
    };

    it('should generate interpretation from traffic stat data', async () => {
      mockedApi.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await generateIntersectionTrafficInterpretation(
        1,
        '2024-01-15T10:00:00Z',
        mockTrafficStat
      );

      expect(mockedApi.post).toHaveBeenCalledWith(
        'traffic/generate-interpretation/',
        {
          intersection_id: 1,
          datetime: '2024-01-15T10:00:00Z',
          traffic_volumes: {
            NS: 150,
            SN: 120,
            EW: 200,
            WE: 180
          },
          total_volume: 650,
          average_speed: 45
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle missing traffic stat data', async () => {
      await expect(generateIntersectionTrafficInterpretation(1, '2024-01-15T10:00:00Z', null))
        .rejects
        .toThrow('교통 통계 데이터가 없습니다.');
    });

    it('should handle traffic stat with missing fields', async () => {
      const incompleteTrafficStat = {
        NS: 150,
        // Missing other fields
      };

      mockedApi.post.mockResolvedValueOnce({ data: mockResponse });

      await generateIntersectionTrafficInterpretation(
        1,
        '2024-01-15T10:00:00Z',
        incompleteTrafficStat
      );

      expect(mockedApi.post).toHaveBeenCalledWith(
        'traffic/generate-interpretation/',
        {
          intersection_id: 1,
          datetime: '2024-01-15T10:00:00Z',
          traffic_volumes: {
            NS: 150,
            SN: 0,
            EW: 0,
            WE: 0
          },
          total_volume: 0,
          average_speed: 0
        }
      );
    });
  });
});