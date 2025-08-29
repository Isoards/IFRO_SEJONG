import React, { useRef, useState } from 'react';
import { PDFTemplate } from './PDFTemplate';
import { usePDFGeneration } from '../../utils/usePDFGeneration';
import { ReportData, AITrafficAnalysis } from '../../types/global.types';
import { generateAITrafficAnalysis } from '../../api/intersections';

interface EnhancedPDFGeneratorProps {
  reportData: ReportData;
  className?: string;
  includeAIAnalysis?: boolean;
  timePeriod?: string;
}

/**
 * Enhanced PDF Generator with AI Analysis
 * Generates PDF reports with optional AI-powered traffic analysis
 */
export const EnhancedPDFGenerator: React.FC<EnhancedPDFGeneratorProps> = ({
  reportData,
  className = '',
  includeAIAnalysis = true,
  timePeriod = "24h",
}) => {
  const templateRef = useRef<HTMLDivElement>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AITrafficAnalysis | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  
  const {
    status,
    generatePDF,
    generatePreview,
    resetStatus,
    isSupported,
  } = usePDFGeneration({
    config: {
      format: 'A4',
      orientation: 'portrait',
      quality: 1.0,
    },
    onSuccess: () => {
      console.log('Enhanced PDF generated successfully!');
    },
    onError: (error) => {
      console.error('Enhanced PDF generation failed:', error);
    },
  });

  const loadAIAnalysis = async () => {
    if (!includeAIAnalysis || !reportData.intersection?.id) return;

    setIsLoadingAI(true);
    setAiError(null);

    try {
      const response = await generateAITrafficAnalysis(reportData.intersection.id, timePeriod);
      setAiAnalysis(response.analysis);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate AI analysis';
      setAiError(errorMessage);
      console.error('AI Analysis Error:', error);
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleGeneratePDF = async () => {
    if (!templateRef.current) {
      console.error('Template element not found');
      return;
    }

    // Load AI analysis if enabled and not already loaded
    if (includeAIAnalysis && !aiAnalysis && !isLoadingAI) {
      await loadAIAnalysis();
    }

    await generatePDF(reportData, templateRef.current);
  };

  const handleGeneratePreview = async () => {
    if (!templateRef.current) {
      console.error('Template element not found');
      return;
    }

    // Load AI analysis if enabled and not already loaded
    if (includeAIAnalysis && !aiAnalysis && !isLoadingAI) {
      await loadAIAnalysis();
    }

    const previewUrl = await generatePreview(reportData, templateRef.current);
    if (previewUrl) {
      const previewWindow = window.open();
      if (previewWindow) {
        previewWindow.document.write(`
          <html>
            <head><title>Enhanced PDF Preview</title></head>
            <body style="margin:0;padding:20px;">
              <iframe src="${previewUrl}" width="100%" height="800px" frameborder="0"></iframe>
            </body>
          </html>
        `);
      }
    }
  };

  const handleToggleAI = () => {
    if (!includeAIAnalysis) {
      loadAIAnalysis();
    } else {
      setAiAnalysis(null);
      setAiError(null);
    }
  };

  if (!isSupported) {
    return (
      <div className={`enhanced-pdf-generator ${className}`}>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> PDF generation is not supported in this browser.
        </div>
      </div>
    );
  }

  return (
    <div className={`enhanced-pdf-generator ${className}`}>
      {/* Control Panel */}
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Enhanced PDF Generation Controls</h3>
        
        {/* AI Analysis Toggle */}
        <div className="mb-4 p-3 bg-white rounded border">
          <div className="flex items-center justify-between mb-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={includeAIAnalysis}
                onChange={handleToggleAI}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm font-medium">Include AI Analysis</span>
            </label>
            
            {includeAIAnalysis && (
              <select
                value={timePeriod}
                onChange={(e) => {
                  // Reset AI analysis when time period changes
                  setAiAnalysis(null);
                  setAiError(null);
                }}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            )}
          </div>

          {/* AI Status */}
          {includeAIAnalysis && (
            <div className="text-sm">
              {isLoadingAI && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Loading AI analysis...</span>
                </div>
              )}
              
              {aiAnalysis && (
                <div className="text-green-600">
                  ✓ AI analysis loaded successfully
                </div>
              )}
              
              {aiError && (
                <div className="text-red-600">
                  ⚠ AI analysis failed: {aiError}
                </div>
              )}
              
              {!aiAnalysis && !isLoadingAI && !aiError && (
                <div className="text-gray-600">
                  AI analysis will be loaded when generating PDF
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="flex gap-4 mb-4">
          <button
            onClick={handleGeneratePDF}
            disabled={status.isGenerating || isLoadingAI}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status.isGenerating ? 'Generating...' : 'Generate Enhanced PDF'}
          </button>
          
          <button
            onClick={handleGeneratePreview}
            disabled={status.isGenerating || isLoadingAI}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Preview Enhanced PDF
          </button>
          
          {includeAIAnalysis && !aiAnalysis && (
            <button
              onClick={loadAIAnalysis}
              disabled={isLoadingAI}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoadingAI ? 'Loading AI...' : 'Load AI Analysis'}
            </button>
          )}
          
          <button
            onClick={resetStatus}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
        </div>

        {/* Status Display */}
        {(status.isGenerating || isLoadingAI) && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-gray-600">
                {isLoadingAI ? 'Loading AI analysis...' : `Generating PDF... ${status.progress}%`}
              </span>
            </div>
            {!isLoadingAI && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${status.progress}%` }}
                ></div>
              </div>
            )}
          </div>
        )}

        {status.completed && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <strong>성공:</strong> AI 분석이 포함된 PDF가 생성되어 다운로드되었습니다!
          </div>
        )}

        {(status.error || aiError) && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong>오류:</strong> {status.error || aiError}
            {aiError && (
              <div className="mt-2 text-sm">
                AI 분석 없이 기본 PDF를 생성하려면 "Include AI Analysis" 옵션을 해제하고 다시 시도해주세요.
              </div>
            )}
          </div>
        )}
      </div>

      {/* PDF Template Preview */}
      <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Enhanced PDF Template Preview</h3>
        <div className="transform scale-50 origin-top-left" style={{ width: '200%', height: '200%' }}>
          <div ref={templateRef}>
            <PDFTemplate 
              reportData={reportData} 
              aiAnalysis={aiAnalysis || undefined}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedPDFGenerator;