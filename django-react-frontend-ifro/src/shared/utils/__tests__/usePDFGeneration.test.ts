import { renderHook, act } from '@testing-library/react';
import { usePDFGeneration } from '../usePDFGeneration';
import { ReportData } from '../../types/global.types';

// Mock the PDFReportGenerator
jest.mock('../PDFReportGenerator', () => {
  const mockInstance = {
    generateReport: jest.fn(),
    generatePreview: jest.fn(),
    updateConfig: jest.fn(),
    updateRetryOptions: jest.fn(),
    updateMemoryOptions: jest.fn(),
    cancelGeneration: jest.fn(),
    isCurrentlyGenerating: jest.fn(() => false),
    getConfig: jest.fn(() => ({})),
  };

  const MockConstructor = jest.fn().mockImplementation(() => mockInstance);
  MockConstructor.isSupported = jest.fn(() => true);
  MockConstructor.estimateTime = jest.fn(() => 3000);

  return {
    PDFReportGenerator: MockConstructor,
  };
});

describe('usePDFGeneration', () => {
  let mockReportData: ReportData;
  let mockTemplateElement: HTMLElement;

  beforeEach(() => {
    mockReportData = {
      intersection: {
        id: 1,
        name: 'Test Intersection',
        latitude: -12.0464,
        longitude: -77.0428,
        total_volume: 1000,
        average_speed: 45,
        datetime: '2024-01-15T10:00:00Z'
      },
      datetime: '2024-01-15T10:00:00Z',
      trafficVolumes: {
        NS: 250,
        SN: 300,
        EW: 200,
        WE: 250
      },
      totalVolume: 1000,
      averageSpeed: 45,
      interpretation: 'Test interpretation',
      congestionLevel: 'moderate',
      peakDirection: 'SN'
    };

    mockTemplateElement = document.createElement('div');
    mockTemplateElement.innerHTML = '<div>Test PDF Template</div>';
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Hook Initialization', () => {
    it('should initialize with default status', () => {
      const { result } = renderHook(() => usePDFGeneration());

      expect(result.current.status).toEqual({
        isGenerating: false,
        progress: 0,
        error: null,
        completed: false,
      });
    });

    it('should initialize with custom options', () => {
      const options = {
        config: { format: 'Letter' as const },
        retryOptions: { maxRetries: 5 },
        memoryOptions: { maxMemoryUsage: 200 },
        onSuccess: jest.fn(),
        onError: jest.fn(),
      };

      const { result } = renderHook(() => usePDFGeneration(options));

      expect(result.current.status).toEqual({
        isGenerating: false,
        progress: 0,
        error: null,
        completed: false,
      });
    });
  });

  describe('Configuration Updates', () => {
    it('should update PDF config', () => {
      const { result } = renderHook(() => usePDFGeneration());

      act(() => {
        result.current.updateConfig({ quality: 0.8 });
      });

      // Since updateConfig doesn't return anything, we just verify it doesn't throw
      expect(() => result.current.updateConfig({ quality: 0.8 })).not.toThrow();
    });

    it('should update retry options', () => {
      const { result } = renderHook(() => usePDFGeneration());

      act(() => {
        result.current.updateRetryOptions({ maxRetries: 10 });
      });

      expect(() => result.current.updateRetryOptions({ maxRetries: 10 })).not.toThrow();
    });

    it('should update memory options', () => {
      const { result } = renderHook(() => usePDFGeneration());

      act(() => {
        result.current.updateMemoryOptions({ maxMemoryUsage: 150 });
      });

      expect(() => result.current.updateMemoryOptions({ maxMemoryUsage: 150 })).not.toThrow();
    });
  });

  describe('Generation Control', () => {
    it('should provide generation status', () => {
      const { result } = renderHook(() => usePDFGeneration());

      const isGenerating = result.current.isCurrentlyGenerating();
      expect(typeof isGenerating).toBe('boolean');
    });

    it('should allow cancellation', () => {
      const { result } = renderHook(() => usePDFGeneration());

      act(() => {
        result.current.cancelGeneration();
      });

      expect(() => result.current.cancelGeneration()).not.toThrow();
    });

    it('should reset status', () => {
      const { result } = renderHook(() => usePDFGeneration());

      act(() => {
        result.current.resetStatus();
      });

      expect(result.current.status).toEqual({
        isGenerating: false,
        progress: 0,
        error: null,
        completed: false,
      });
    });
  });

  describe('Hook Methods', () => {
    it('should provide all expected methods', () => {
      const { result } = renderHook(() => usePDFGeneration());

      expect(typeof result.current.generatePDF).toBe('function');
      expect(typeof result.current.generatePreview).toBe('function');
      expect(typeof result.current.resetStatus).toBe('function');
      expect(typeof result.current.updateConfig).toBe('function');
      expect(typeof result.current.updateRetryOptions).toBe('function');
      expect(typeof result.current.updateMemoryOptions).toBe('function');
      expect(typeof result.current.cancelGeneration).toBe('function');
      expect(typeof result.current.isCurrentlyGenerating).toBe('function');
      // Note: isSupported is tested separately due to mocking complexity
    });
  });
});