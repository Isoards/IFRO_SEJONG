import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { ReportData } from '../types/global.types';
import { usePDFGeneration } from '../utils/usePDFGeneration';
import { useTranslation } from 'react-i18next';

interface PDFStatusOptions {
  autoHideDelay?: {
    success: number;
    error: number;
    info: number;
  };
  onSuccess?: () => void;
  onError?: (error: string) => void;
  onRetry?: (attempt: number) => void;
  onProgress?: (progress: number) => void;
  maxRetries?: number;
}

interface PDFStatusFeedback {
  type: 'success' | 'error' | 'info' | 'warning' | null;
  message: string;
  isVisible: boolean;
  autoHide?: boolean;
}

/**
 * Enhanced hook for PDF generation with improved status management and user feedback
 * 
 * This hook provides:
 * - PDF generation status tracking
 * - User feedback messages (success, error, info)
 * - Automatic retry functionality
 * - Progress tracking
 * - Localized messages
 */
export const usePDFGenerationStatus = (options: PDFStatusOptions = {}) => {
  const { t } = useTranslation();
  
  // Default options - memoized to prevent unnecessary re-renders
  const defaultOptions = useMemo(() => ({
    autoHideDelay: {
      success: 3000,
      error: 8000,
      info: 5000,
    },
    maxRetries: 3,
    ...options,
  }), [options]);

  // User feedback state
  const [feedback, setFeedback] = useState<PDFStatusFeedback>({
    type: null,
    message: '',
    isVisible: false,
  });

  // Retry state
  const [retryCount, setRetryCount] = useState(0);
  const [maxRetries] = useState(defaultOptions.maxRetries || 3);
  
  // Auto-hide timer reference
  const autoHideTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Last generation attempt reference
  const lastGenerationRef = useRef<{
    reportData: ReportData | null;
    templateElement: HTMLElement | null;
  }>({
    reportData: null,
    templateElement: null,
  });

  // Use the base PDF generation hook
  const pdfGeneration = usePDFGeneration({
    onSuccess: () => {
      showSuccessFeedback(t('reports.pdfDownloadSuccess') || 'PDF downloaded successfully!');
      if (defaultOptions.onSuccess) {
        defaultOptions.onSuccess();
      }
    },
    onError: (error: string) => {
      showErrorFeedback(error || t('reports.pdfGenerationFailed') || 'Failed to generate PDF');
      if (defaultOptions.onError) {
        defaultOptions.onError(error);
      }
    },
    onRetry: (attempt: number, error: string) => {
      const retryMessage = t('reports.retryingGeneration', { attempt, maxRetries }) || 
        `Retrying PDF generation (${attempt}/${maxRetries})...`;
      showInfoFeedback(retryMessage);
      setRetryCount(attempt);
      if (defaultOptions.onRetry) {
        defaultOptions.onRetry(attempt);
      }
    },
  });

  // Watch for progress changes and notify
  useEffect(() => {
    if (defaultOptions.onProgress && pdfGeneration.status.progress > 0) {
      defaultOptions.onProgress(pdfGeneration.status.progress);
    }
  }, [pdfGeneration.status.progress, defaultOptions.onProgress, defaultOptions]);

  // Clear auto-hide timer when component unmounts
  useEffect(() => {
    return () => {
      if (autoHideTimerRef.current) {
        clearTimeout(autoHideTimerRef.current);
      }
    };
  }, []);

  // Show success feedback with auto-hide
  const showSuccessFeedback = useCallback((message: string, autoHide: boolean = true) => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    setFeedback({
      type: 'success',
      message,
      isVisible: true,
      autoHide,
    });
    
    // Auto-hide after delay if enabled
    if (autoHide && defaultOptions.autoHideDelay?.success) {
      autoHideTimerRef.current = setTimeout(() => {
        setFeedback(prev => ({...prev, isVisible: false}));
        autoHideTimerRef.current = null;
      }, defaultOptions.autoHideDelay.success);
    }
  }, [defaultOptions.autoHideDelay?.success]);

  // Show error feedback with auto-hide
  const showErrorFeedback = useCallback((message: string, autoHide: boolean = true) => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    setFeedback({
      type: 'error',
      message,
      isVisible: true,
      autoHide,
    });
    
    // Auto-hide after delay if enabled
    if (autoHide && defaultOptions.autoHideDelay?.error) {
      autoHideTimerRef.current = setTimeout(() => {
        setFeedback(prev => ({...prev, isVisible: false}));
        autoHideTimerRef.current = null;
      }, defaultOptions.autoHideDelay.error);
    }
  }, [defaultOptions.autoHideDelay?.error]);

  // Show info feedback
  const showInfoFeedback = useCallback((message: string, autoHide: boolean = true) => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    setFeedback({
      type: 'info',
      message,
      isVisible: true,
      autoHide,
    });
    
    // Auto-hide after delay if enabled
    if (autoHide && defaultOptions.autoHideDelay?.info) {
      autoHideTimerRef.current = setTimeout(() => {
        setFeedback(prev => ({...prev, isVisible: false}));
        autoHideTimerRef.current = null;
      }, defaultOptions.autoHideDelay.info);
    }
  }, [defaultOptions.autoHideDelay?.info]);

  // Show warning feedback
  const showWarningFeedback = useCallback((message: string, autoHide: boolean = true) => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    setFeedback({
      type: 'warning',
      message,
      isVisible: true,
      autoHide,
    });
    
    // Auto-hide after delay if enabled
    if (autoHide && defaultOptions.autoHideDelay?.info) {
      autoHideTimerRef.current = setTimeout(() => {
        setFeedback(prev => ({...prev, isVisible: false}));
        autoHideTimerRef.current = null;
      }, defaultOptions.autoHideDelay.info);
    }
  }, [defaultOptions.autoHideDelay?.info]);

  // Hide feedback
  const hideFeedback = useCallback(() => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    setFeedback(prev => ({...prev, isVisible: false}));
  }, []);

  // Generate PDF with saved parameters for retry
  const generatePDF = useCallback(async (
    reportData: ReportData,
    templateElement: HTMLElement
  ) => {
    // Save parameters for potential retry
    lastGenerationRef.current = {
      reportData,
      templateElement,
    };
    
    // Reset retry count
    setRetryCount(0);
    
    // Show starting message
    showInfoFeedback(t('reports.startingGeneration') || 'Starting PDF generation...');
    
    try {
      await pdfGeneration.generatePDF(reportData, templateElement);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      showErrorFeedback(`${t('reports.generationError') || 'Error'}: ${errorMessage}`);
    }
  }, [pdfGeneration, showInfoFeedback, showErrorFeedback, t]);

  // Retry generation
  const retryGeneration = useCallback(async () => {
    const { reportData, templateElement } = lastGenerationRef.current;
    
    if (!reportData || !templateElement) {
      showErrorFeedback(t('reports.noDataForRetry') || 'No data available for retry');
      return;
    }
    
    if (retryCount >= maxRetries) {
      showErrorFeedback(
        t('reports.maxRetriesReached', { maxRetries }) || 
        `Maximum retry attempts (${maxRetries}) reached. Please try again later.`
      );
      return;
    }
    
    setRetryCount(prev => prev + 1);
    const newRetryCount = retryCount + 1;
    
    showInfoFeedback(
      t('reports.retryingGeneration', { attempt: newRetryCount, maxRetries }) || 
      `Retrying PDF generation (${newRetryCount}/${maxRetries})...`
    );
    
    try {
      await pdfGeneration.generatePDF(reportData, templateElement);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      showErrorFeedback(
        t('reports.retryFailed', { error: errorMessage }) || 
        `Retry failed: ${errorMessage}`
      );
    }
  }, [retryCount, maxRetries, pdfGeneration, showInfoFeedback, showErrorFeedback, t]);

  // Reset all states
  const resetAll = useCallback(() => {
    // Clear any existing timer
    if (autoHideTimerRef.current) {
      clearTimeout(autoHideTimerRef.current);
      autoHideTimerRef.current = null;
    }
    
    pdfGeneration.resetStatus();
    setFeedback({
      type: null,
      message: '',
      isVisible: false,
    });
    setRetryCount(0);
    
    // Clear saved generation parameters
    lastGenerationRef.current = {
      reportData: null,
      templateElement: null,
    };
  }, [pdfGeneration]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      // Cancel any ongoing generation when component unmounts
      if (pdfGeneration.isCurrentlyGenerating()) {
        pdfGeneration.cancelGeneration();
      }
      
      // Clear any existing timer
      if (autoHideTimerRef.current) {
        clearTimeout(autoHideTimerRef.current);
      }
    };
  }, [pdfGeneration]);

  return {
    ...pdfGeneration,
    generatePDF, // Override with our version that saves parameters
    feedback,
    retryCount,
    maxRetries,
    showSuccessFeedback,
    showErrorFeedback,
    showInfoFeedback,
    showWarningFeedback,
    hideFeedback,
    retryGeneration,
    resetAll,
    isPdfSupported: pdfGeneration.isSupported,
  };
};