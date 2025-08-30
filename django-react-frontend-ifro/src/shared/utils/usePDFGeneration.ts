import { useState, useCallback, useRef, useEffect } from 'react';
import { PDFGenerationStatus, ReportData, PDFConfig } from '../types/global.types';
import { PDFReportGenerator } from './PDFReportGenerator';

interface RetryOptions {
  maxRetries: number;
  retryDelay: number;
  backoffMultiplier: number;
}

interface MemoryOptimizationOptions {
  enableGarbageCollection: boolean;
  chunkSize: number;
  maxMemoryUsage: number; // in MB
}

interface UsePDFGenerationOptions {
  config?: Partial<PDFConfig>;
  retryOptions?: Partial<RetryOptions>;
  memoryOptions?: Partial<MemoryOptimizationOptions>;
  onSuccess?: () => void;
  onError?: (error: string) => void;
  onRetry?: (attempt: number, error: string) => void;
}

export const usePDFGeneration = (options: UsePDFGenerationOptions = {}) => {
  const [status, setStatus] = useState<PDFGenerationStatus>({
    isGenerating: false,
    progress: 0,
    error: null,
    completed: false,
  });

  const generatorRef = useRef<PDFReportGenerator | null>(null);
  const onSuccessRef = useRef(options.onSuccess);
  const onErrorRef = useRef(options.onError);

  // Update callback refs when options change
  useEffect(() => {
    onSuccessRef.current = options.onSuccess;
    onErrorRef.current = options.onError;
  });

  // Initialize generator only once
  useEffect(() => {
    if (!generatorRef.current) {
      generatorRef.current = new PDFReportGenerator(
        options.config || {},
        (newStatus) => {
          setStatus(newStatus);

          if (newStatus.completed && onSuccessRef.current) {
            onSuccessRef.current();
          }

          if (newStatus.error && onErrorRef.current) {
            onErrorRef.current(newStatus.error);
          }
        },
        options.retryOptions || {},
        options.memoryOptions || {}
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - initialize only once

  const generatePDF = useCallback(async (
    reportData: ReportData,
    templateElement: HTMLElement
  ) => {
    try {
      if (!generatorRef.current) {
        throw new Error('PDF generator not initialized');
      }
      await generatorRef.current.generateReport(reportData, templateElement);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setStatus(prev => ({
        ...prev,
        isGenerating: false,
        error: errorMessage,
      }));

      if (onErrorRef.current) {
        onErrorRef.current(errorMessage);
      }
    }
  }, []);

  const generatePreview = useCallback(async (
    reportData: ReportData,
    templateElement: HTMLElement
  ): Promise<string | null> => {
    try {
      if (!generatorRef.current) {
        throw new Error('PDF generator not initialized');
      }
      return await generatorRef.current.generatePreview(reportData, templateElement);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setStatus(prev => ({
        ...prev,
        error: errorMessage,
      }));

      if (onErrorRef.current) {
        onErrorRef.current(errorMessage);
      }

      return null;
    }
  }, []);

  const resetStatus = useCallback(() => {
    setStatus({
      isGenerating: false,
      progress: 0,
      error: null,
      completed: false,
    });
  }, []);

  const updateConfig = useCallback((newConfig: Partial<PDFConfig>) => {
    if (generatorRef.current) {
      generatorRef.current.updateConfig(newConfig);
    }
  }, []);

  const updateRetryOptions = useCallback((newRetryOptions: Partial<RetryOptions>) => {
    if (generatorRef.current) {
      generatorRef.current.updateRetryOptions(newRetryOptions);
    }
  }, []);

  const updateMemoryOptions = useCallback((newMemoryOptions: Partial<MemoryOptimizationOptions>) => {
    if (generatorRef.current) {
      generatorRef.current.updateMemoryOptions(newMemoryOptions);
    }
  }, []);

  const cancelGeneration = useCallback(() => {
    if (generatorRef.current) {
      generatorRef.current.cancelGeneration();
    }
  }, []);

  const isCurrentlyGenerating = useCallback(() => {
    return generatorRef.current?.isCurrentlyGenerating() || false;
  }, []);

  const isSupported = PDFReportGenerator.isSupported();

  return {
    status,
    generatePDF,
    generatePreview,
    resetStatus,
    updateConfig,
    updateRetryOptions,
    updateMemoryOptions,
    cancelGeneration,
    isCurrentlyGenerating,
    isSupported,
  };
};