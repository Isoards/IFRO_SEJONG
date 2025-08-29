import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, Loader2, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { ProgressIndicator } from '../common/ProgressIndicator';
import { FeedbackMessage } from '../common/FeedbackMessage';
import { PDFGenerationStatus as PDFStatus } from '../../types/global.types';

interface PDFGenerationStatusProps {
  status: PDFStatus;
  feedback: {
    type: 'success' | 'error' | 'info' | 'warning' | null;
    message: string;
    isVisible: boolean;
    autoHide?: boolean;
  };
  onDownload: () => void;
  onRetry?: () => void;
  onDismissFeedback?: () => void;
  retryCount?: number;
  maxRetries?: number;
  isPdfSupported: boolean;
  hasData: boolean;
  compact?: boolean; // New prop for compact mode
}

/**
 * Component for displaying PDF generation status and providing user feedback
 * 
 * Features:
 * - Download button with loading state
 * - Progress indicator with percentage
 * - Retry functionality for failed generations
 * - Status messages for success/error/info
 * - Browser compatibility check
 * - Data availability check
 */
export const PDFGenerationStatus: React.FC<PDFGenerationStatusProps> = ({
  status,
  feedback,
  onDownload,
  onRetry,
  onDismissFeedback,
  retryCount = 0,
  maxRetries = 3,
  isPdfSupported,
  hasData,
  compact = false,
}) => {
  const { t } = useTranslation();
  const [showProgressLabel, setShowProgressLabel] = useState(false);
  
  // Show progress label after a short delay to avoid flickering for quick operations
  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (status.isGenerating && status.progress > 0) {
      timer = setTimeout(() => {
        setShowProgressLabel(true);
      }, 500);
    } else {
      setShowProgressLabel(false);
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [status.isGenerating, status.progress]);

  // Get button text based on generation status
  const getButtonText = () => {
    if (status.isGenerating) {
      if (status.progress < 10) {
        return t("reports.preparing") || "Preparing...";
      } else if (status.progress < 50) {
        return t("reports.generating") || "Generating...";
      } else if (status.progress < 90) {
        return t("reports.processing") || "Processing...";
      } else {
        return t("reports.finalizing") || "Finalizing...";
      }
    }
    return t("reports.downloadPdf") || "Download PDF";
  };

  // Get status icon based on generation state
  const getStatusIcon = () => {
    if (status.isGenerating) {
      return <Loader2 size={16} className="animate-spin" />;
    } else if (status.error) {
      return <AlertTriangle size={16} className="text-red-500" />;
    } else if (status.completed) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    return <Download size={16} />;
  };

  // Compact mode for header placement
  if (compact) {
    return (
      <button
        onClick={onDownload}
        disabled={!isPdfSupported || status.isGenerating || !hasData}
        className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        aria-label={String(status.isGenerating ? (t("reports.generating") || 'Generating') : (t("reports.downloadPdf") || 'Download PDF'))}
        title={String(status.isGenerating ? (t("reports.generating") || 'Generating') : (t("reports.downloadPdf") || 'Download PDF'))}
      >
        {getStatusIcon()}
        <span className="text-sm">{status.isGenerating ? t("reports.generating") || "Generating..." : t("reports.downloadPdf") || "PDF"}</span>
      </button>
    );
  }

  return (
    <div className="space-y-4">
      {/* Download Button with Status */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onDownload}
          disabled={!isPdfSupported || status.isGenerating || !hasData}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          aria-label={String(status.isGenerating ? (t("reports.generating") || 'Generating') : (t("reports.downloadPdf") || 'Download PDF'))}
        >
          {getStatusIcon()}
          <span>{getButtonText()}</span>
        </button>
        
        {/* Retry Button - Only show when there's an error and retry is available */}
        {status.error && onRetry && retryCount < maxRetries && (
          <button
            onClick={onRetry}
            disabled={status.isGenerating}
            className="flex items-center space-x-1 px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 disabled:opacity-50 text-sm font-medium"
            aria-label={String(t("common.retry") || 'Retry')}
          >
            <RefreshCw size={14} />
            <span className="text-sm">
              {t("reports.retryWithCount", { count: retryCount, max: maxRetries }) || 
                `Retry (${retryCount}/${maxRetries})`}
            </span>
          </button>
        )}
      </div>
      
      {/* Progress Indicator with Label */}
      {status.isGenerating && status.progress > 0 && (
        <div className="space-y-1">
          <ProgressIndicator progress={status.progress} />
          {showProgressLabel && (
            <div className="flex justify-between text-xs text-gray-500">
              <span>{t("reports.generatingPdf") || "Generating PDF"}</span>
              <span>{Math.round(status.progress)}%</span>
            </div>
          )}
        </div>
      )}
      
      {/* Feedback Messages */}
      <FeedbackMessage
        type={feedback.type}
        message={feedback.message}
        isVisible={feedback.isVisible}
        onDismiss={onDismissFeedback}
        autoHideDuration={feedback.autoHide ? 
          feedback.type === 'success' ? 3000 : 
          feedback.type === 'error' ? 8000 : 5000 
          : undefined}
      />
      
      {/* Browser Support Warning */}
      {!isPdfSupported && (
        <FeedbackMessage
          type="error"
          message={t("reports.browserNotSupported") || "PDF generation is not supported in this browser"}
          isVisible={true}
          showCloseButton={false}
        />
      )}
      
      {/* No Data Warning */}
      {!hasData && (
        <FeedbackMessage
          type="info"
          message={t("reports.noDataAvailable") || "No traffic data available for PDF generation"}
          isVisible={true}
          showCloseButton={false}
        />
      )}
      
      {/* Retry Count Indicator - Only show when retries have been attempted */}
      {retryCount > 0 && !status.isGenerating && !status.completed && (
        <div className="text-xs text-gray-500">
          {t("reports.retryAttempts", { count: retryCount, max: maxRetries }) || 
            `Retry attempts: ${retryCount}/${maxRetries}`}
        </div>
      )}
    </div>
  );
};