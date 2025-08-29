import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PDFGenerationStatus } from '../PDFGenerationStatus';
import { PDFGenerationStatus as PDFStatus } from '../../../types/global.types';

// Mock react-i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      const translations: Record<string, string> = {
        'reports.downloadPdf': 'Download PDF',
        'reports.generating': 'Generating...',
        'reports.preparing': 'Preparing...',
        'reports.processing': 'Processing...',
        'reports.finalizing': 'Finalizing...',
        'reports.generatingPdf': 'Generating PDF',
        'reports.retryWithCount': `Retry (${options?.count}/${options?.max})`,
        'reports.retryAttempts': `Retry attempts: ${options?.count}/${options?.max}`,
        'reports.browserNotSupported': 'PDF generation is not supported in this browser',
        'reports.noDataAvailable': 'No traffic data available for PDF generation',
        'common.retry': 'Retry'
      };
      return translations[key] || key;
    }
  })
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Download: ({ size, className }: any) => <div data-testid="download-icon" className={className} />,
  Loader2: ({ size, className }: any) => <div data-testid="loader-icon" className={className} />,
  RefreshCw: ({ size, className }: any) => <div data-testid="refresh-icon" className={className} />,
  AlertTriangle: ({ size, className }: any) => <div data-testid="alert-icon" className={className} />,
  CheckCircle2: ({ size, className }: any) => <div data-testid="check-icon" className={className} />
}));

// Mock common components
jest.mock('../../common/Button', () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={className}
      data-testid="button"
      {...props}
    >
      {children}
    </button>
  )
}));

jest.mock('../../common/ProgressIndicator', () => ({
  ProgressIndicator: ({ progress }: any) => (
    <div data-testid="progress-indicator" data-progress={progress}>
      Progress: {progress}%
    </div>
  )
}));

jest.mock('../../common/FeedbackMessage', () => ({
  FeedbackMessage: ({ type, message, isVisible, onDismiss, showCloseButton }: any) => (
    isVisible ? (
      <div data-testid="feedback-message" data-type={type}>
        {message}
        {showCloseButton !== false && onDismiss && (
          <button onClick={onDismiss} data-testid="dismiss-feedback">×</button>
        )}
      </div>
    ) : null
  )
}));

describe('PDFGenerationStatus', () => {
  const defaultProps = {
    status: {
      isGenerating: false,
      progress: 0,
      error: null,
      completed: false
    } as PDFStatus,
    feedback: {
      type: null as any,
      message: '',
      isVisible: false
    },
    onDownload: jest.fn(),
    isPdfSupported: true,
    hasData: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Download Button', () => {
    it('renders download button with correct text', () => {
      render(<PDFGenerationStatus {...defaultProps} />);
      
      expect(screen.getByTestId('button')).toBeInTheDocument();
      expect(screen.getByText('Download PDF')).toBeInTheDocument();
      expect(screen.getByTestId('download-icon')).toBeInTheDocument();
    });

    it('calls onDownload when button is clicked', () => {
      const onDownload = jest.fn();
      render(<PDFGenerationStatus {...defaultProps} onDownload={onDownload} />);
      
      fireEvent.click(screen.getByTestId('button'));
      expect(onDownload).toHaveBeenCalledTimes(1);
    });

    it('disables button when PDF is not supported', () => {
      render(<PDFGenerationStatus {...defaultProps} isPdfSupported={false} />);
      
      expect(screen.getByTestId('button')).toBeDisabled();
    });

    it('disables button when no data is available', () => {
      render(<PDFGenerationStatus {...defaultProps} hasData={false} />);
      
      expect(screen.getByTestId('button')).toBeDisabled();
    });

    it('disables button when generating', () => {
      const status = { ...defaultProps.status, isGenerating: true };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByTestId('button')).toBeDisabled();
    });
  });

  describe('Generation Status', () => {
    it('shows preparing text when progress is low', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 5 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByText('Preparing...')).toBeInTheDocument();
      expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
    });

    it('shows generating text when progress is medium', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 30 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByText('Generating...')).toBeInTheDocument();
    });

    it('shows processing text when progress is high', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 70 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('shows finalizing text when progress is very high', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 95 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByText('Finalizing...')).toBeInTheDocument();
    });

    it('shows error icon when there is an error', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByTestId('alert-icon')).toBeInTheDocument();
    });

    it('shows success icon when completed', () => {
      const status = { ...defaultProps.status, completed: true };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByTestId('check-icon')).toBeInTheDocument();
    });
  });

  describe('Progress Indicator', () => {
    it('shows progress indicator when generating', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 50 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByTestId('progress-indicator')).toBeInTheDocument();
      expect(screen.getByTestId('progress-indicator')).toHaveAttribute('data-progress', '50');
    });

    it('does not show progress indicator when not generating', () => {
      render(<PDFGenerationStatus {...defaultProps} />);
      
      expect(screen.queryByTestId('progress-indicator')).not.toBeInTheDocument();
    });

    it('shows progress percentage', () => {
      const status = { ...defaultProps.status, isGenerating: true, progress: 50 };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByText('Progress: 50%')).toBeInTheDocument();
    });
  });

  describe('Retry Functionality', () => {
    it('shows retry button when there is an error and retry is available', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      const onRetry = jest.fn();
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          status={status} 
          onRetry={onRetry}
          retryCount={1}
          maxRetries={3}
        />
      );
      
      expect(screen.getByText('Retry (1/3)')).toBeInTheDocument();
      expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      const onRetry = jest.fn();
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          status={status} 
          onRetry={onRetry}
        />
      );
      
      const retryButton = screen.getAllByTestId('button')[1]; // Second button is retry
      fireEvent.click(retryButton);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('does not show retry button when max retries reached', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          status={status} 
          onRetry={jest.fn()}
          retryCount={3}
          maxRetries={3}
        />
      );
      
      // Should not show retry button, but retry count indicator may still be visible
      const retryButtons = screen.queryAllByText(/Retry \(/);
      expect(retryButtons).toHaveLength(0);
    });

    it('shows retry count indicator when retries have been attempted', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          status={status} 
          retryCount={2}
          maxRetries={3}
        />
      );
      
      expect(screen.getByText('Retry attempts: 2/3')).toBeInTheDocument();
    });
  });

  describe('Feedback Messages', () => {
    it('shows feedback message when visible', () => {
      const feedback = {
        type: 'success' as const,
        message: 'PDF generated successfully',
        isVisible: true
      };
      
      render(<PDFGenerationStatus {...defaultProps} feedback={feedback} />);
      
      expect(screen.getByTestId('feedback-message')).toBeInTheDocument();
      expect(screen.getByText('PDF generated successfully')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-message')).toHaveAttribute('data-type', 'success');
    });

    it('calls onDismissFeedback when dismiss button is clicked', () => {
      const feedback = {
        type: 'error' as const,
        message: 'Generation failed',
        isVisible: true
      };
      const onDismissFeedback = jest.fn();
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          feedback={feedback}
          onDismissFeedback={onDismissFeedback}
        />
      );
      
      fireEvent.click(screen.getByTestId('dismiss-feedback'));
      expect(onDismissFeedback).toHaveBeenCalledTimes(1);
    });

    it('shows browser not supported warning', () => {
      render(<PDFGenerationStatus {...defaultProps} isPdfSupported={false} />);
      
      expect(screen.getByText('PDF generation is not supported in this browser')).toBeInTheDocument();
    });

    it('shows no data available warning', () => {
      render(<PDFGenerationStatus {...defaultProps} hasData={false} />);
      
      expect(screen.getByText('No traffic data available for PDF generation')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label for download button', () => {
      render(<PDFGenerationStatus {...defaultProps} />);
      
      expect(screen.getByTestId('button')).toHaveAttribute('aria-label', 'Download PDF');
    });

    it('has proper aria-label for generating state', () => {
      const status = { ...defaultProps.status, isGenerating: true };
      render(<PDFGenerationStatus {...defaultProps} status={status} />);
      
      expect(screen.getByTestId('button')).toHaveAttribute('aria-label', 'Generating...');
    });

    it('has proper aria-label for retry button', () => {
      const status = { ...defaultProps.status, error: 'Generation failed' };
      
      render(
        <PDFGenerationStatus 
          {...defaultProps} 
          status={status} 
          onRetry={jest.fn()}
        />
      );
      
      const retryButton = screen.getAllByTestId('button')[1];
      expect(retryButton).toHaveAttribute('aria-label', 'Retry');
    });
  });
});