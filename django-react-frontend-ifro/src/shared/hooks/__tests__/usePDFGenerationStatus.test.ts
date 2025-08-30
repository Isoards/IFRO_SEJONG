import { renderHook, act, waitFor } from '@testing-library/react';
import { usePDFGenerationStatus } from '../usePDFGenerationStatus';
import { usePDFGeneration } from '../../utils/usePDFGeneration';
import { useTranslation } from 'react-i18next';

// Mock dependencies
jest.mock('../../utils/usePDFGeneration');
jest.mock('react-i18next');

const mockUsePDFGeneration = usePDFGeneration as jest.MockedFunction<typeof usePDFGeneration>;
const mockUseTranslation = useTranslation as jest.MockedFunction<typeof useTranslation>;

describe('usePDFGenerationStatus', () => {
  const mockT = jest.fn((key: string, options?: any) => {
    const translations: Record<string, string> = {
      'reports.pdfDownloadSuccess': 'PDF downloaded successfully!',
      'reports.pdfGenerationFailed': 'Failed to generate PDF',
      'reports.startingGeneration': 'Starting PDF generation...',
      'reports.retryingGeneration': `Retrying PDF generation (${options?.attempt}/${options?.maxRetries})...`,
      'reports.noDataForRetry': 'No data available for retry',
      'reports.maxRetriesReached': `Maximum retry attempts (${options?.maxRetries}) reached. Please try again later.`,
      'reports.retryFailed': `Retry failed: ${options?.error}`,
      'reports.generationError': 'Error',
    };
    return translations[key] || key;
  });

  const mockPDFGeneration = {
    status: {
      isGenerating: false,
      progress: 0,
      error: null,
      completed: false,
    },
    generatePDF: jest.fn(),
    resetStatus: jest.fn(),
    isCurrentlyGenerating: jest.fn(() => false),
    cancelGeneration: jest.fn(),
    isSupported: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTranslation.mockReturnValue({
      t: mockT,
      i18n: {} as any,
      ready: true,
    });
    mockUsePDFGeneration.mockReturnValue(mockPDFGeneration);
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    expect(result.current.feedback).toEqual({
      type: null,
      message: '',
      isVisible: false,
    });
    expect(result.current.retryCount).toBe(0);
    expect(result.current.maxRetries).toBe(3);
    expect(result.current.isPdfSupported).toBe(true);
  });

  it('should show success feedback when PDF generation succeeds', async () => {
    const onSuccess = jest.fn();
    const { result } = renderHook(() => usePDFGenerationStatus({ onSuccess }));

    act(() => {
      result.current.showSuccessFeedback('PDF downloaded successfully!');
    });

    expect(result.current.feedback).toEqual({
      type: 'success',
      message: 'PDF downloaded successfully!',
      isVisible: true,
      autoHide: true,
    });
  });

  it('should show error feedback when PDF generation fails', async () => {
    const onError = jest.fn();
    const { result } = renderHook(() => usePDFGenerationStatus({ onError }));

    act(() => {
      result.current.showErrorFeedback('Failed to generate PDF');
    });

    expect(result.current.feedback).toEqual({
      type: 'error',
      message: 'Failed to generate PDF',
      isVisible: true,
      autoHide: true,
    });
  });

  it('should show info feedback during generation', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    act(() => {
      result.current.showInfoFeedback('Starting PDF generation...');
    });

    expect(result.current.feedback).toEqual({
      type: 'info',
      message: 'Starting PDF generation...',
      isVisible: true,
      autoHide: true,
    });
  });

  it('should show warning feedback', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    act(() => {
      result.current.showWarningFeedback('Warning message');
    });

    expect(result.current.feedback).toEqual({
      type: 'warning',
      message: 'Warning message',
      isVisible: true,
      autoHide: true,
    });
  });

  it('should hide feedback when hideFeedback is called', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    act(() => {
      result.current.showSuccessFeedback('Success message');
    });

    expect(result.current.feedback.isVisible).toBe(true);

    act(() => {
      result.current.hideFeedback();
    });

    expect(result.current.feedback.isVisible).toBe(false);
  });

  it('should handle retry generation', async () => {
    const mockReportData = {
      intersection: { id: 1, name: 'Test Intersection' } as any,
      datetime: '2023-01-01T00:00:00Z',
      trafficVolumes: { NS: 100, SN: 200, EW: 150, WE: 180 },
      totalVolume: 630,
      averageSpeed: 45,
    };

    const mockTemplateElement = document.createElement('div');
    
    const { result } = renderHook(() => usePDFGenerationStatus({ maxRetries: 3 }));

    // First, generate PDF to save parameters
    await act(async () => {
      await result.current.generatePDF(mockReportData, mockTemplateElement);
    });

    // Then retry
    await act(async () => {
      await result.current.retryGeneration();
    });

    expect(result.current.retryCount).toBe(1);
    expect(mockPDFGeneration.generatePDF).toHaveBeenCalledTimes(2);
  });

  it('should prevent retry when max retries reached', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus({ maxRetries: 2 }));

    const mockReportData = {
      intersection: { id: 1, name: 'Test Intersection' } as any,
      datetime: '2023-01-01T00:00:00Z',
      trafficVolumes: { NS: 100, SN: 200, EW: 150, WE: 180 },
      totalVolume: 630,
      averageSpeed: 45,
    };

    const mockTemplateElement = document.createElement('div');
    
    // First, generate PDF to save parameters
    await act(async () => {
      await result.current.generatePDF(mockReportData, mockTemplateElement);
    });

    // Retry multiple times to reach max retries
    await act(async () => {
      await result.current.retryGeneration();
    });

    await act(async () => {
      await result.current.retryGeneration();
    });

    // This should now show max retries reached message
    await act(async () => {
      await result.current.retryGeneration();
    });

    expect(result.current.feedback.type).toBe('error');
    expect(result.current.feedback.message).toContain('Maximum retry attempts');
  });

  it('should reset all states when resetAll is called', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    // Set some state
    act(() => {
      result.current.showErrorFeedback('Error message');
    });

    expect(result.current.feedback.isVisible).toBe(true);

    // Reset all
    act(() => {
      result.current.resetAll();
    });

    expect(result.current.feedback).toEqual({
      type: null,
      message: '',
      isVisible: false,
    });
    expect(result.current.retryCount).toBe(0);
    expect(mockPDFGeneration.resetStatus).toHaveBeenCalled();
  });

  it('should handle auto-hide with custom delays', async () => {
    jest.useFakeTimers();
    
    const { result } = renderHook(() => 
      usePDFGenerationStatus({
        autoHideDelay: {
          success: 1000,
          error: 2000,
          info: 1500,
        }
      })
    );

    act(() => {
      result.current.showSuccessFeedback('Success message');
    });

    expect(result.current.feedback.isVisible).toBe(true);

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current.feedback.isVisible).toBe(false);

    jest.useRealTimers();
  });

  it('should call onProgress callback when progress changes', async () => {
    const onProgress = jest.fn();
    
    // Mock progress change
    mockUsePDFGeneration.mockReturnValue({
      ...mockPDFGeneration,
      status: {
        ...mockPDFGeneration.status,
        progress: 50,
      },
    });

    renderHook(() => usePDFGenerationStatus({ onProgress }));

    expect(onProgress).toHaveBeenCalledWith(50);
  });

  it('should handle generation with no data for retry', async () => {
    const { result } = renderHook(() => usePDFGenerationStatus());

    await act(async () => {
      await result.current.retryGeneration();
    });

    expect(result.current.feedback.type).toBe('error');
    expect(result.current.feedback.message).toBe('No data available for retry');
  });

  it('should cleanup timers on unmount', () => {
    jest.useFakeTimers();
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
    
    const { result, unmount } = renderHook(() => usePDFGenerationStatus());

    act(() => {
      result.current.showSuccessFeedback('Success message');
    });

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    jest.useRealTimers();
  });
});