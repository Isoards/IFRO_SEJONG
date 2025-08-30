import React, { useRef } from 'react';
import { PDFTemplate } from './PDFTemplate';
import { usePDFGeneration } from '../../../shared/utils/usePDFGeneration';
import { ReportData } from '../../../shared/types/global.types';

interface PDFGeneratorExampleProps {
  reportData: ReportData;
  className?: string;
}

/**
 * Example component demonstrating PDF generation functionality
 * This can be used as a reference for implementing PDF generation in other components
 */
export const PDFGeneratorExample: React.FC<PDFGeneratorExampleProps> = ({
  reportData,
  className = '',
}) => {
  const templateRef = useRef<HTMLDivElement>(null);
  
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
      console.log('PDF generated successfully!');
    },
    onError: (error) => {
      console.error('PDF generation failed:', error);
    },
  });

  const handleGeneratePDF = async () => {
    if (!templateRef.current) {
      console.error('Template element not found');
      return;
    }

    await generatePDF(reportData, templateRef.current);
  };

  const handleGeneratePreview = async () => {
    if (!templateRef.current) {
      console.error('Template element not found');
      return;
    }

    const previewUrl = await generatePreview(reportData, templateRef.current);
    if (previewUrl) {
      // Open preview in new window
      const previewWindow = window.open();
      if (previewWindow) {
        previewWindow.document.write(`
          <html>
            <head><title>PDF Preview</title></head>
            <body style="margin:0;padding:20px;">
              <iframe src="${previewUrl}" width="100%" height="800px" frameborder="0"></iframe>
            </body>
          </html>
        `);
      }
    }
  };

  if (!isSupported) {
    return (
      <div className={`pdf-generator-example ${className}`}>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> PDF generation is not supported in this browser.
        </div>
      </div>
    );
  }

  return (
    <div className={`pdf-generator-example ${className}`}>
      {/* Control Panel */}
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">PDF Generation Controls</h3>
        
        <div className="flex gap-4 mb-4">
          <button
            onClick={handleGeneratePDF}
            disabled={status.isGenerating}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status.isGenerating ? 'Generating...' : 'Generate PDF'}
          </button>
          
          <button
            onClick={handleGeneratePreview}
            disabled={status.isGenerating}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Preview PDF
          </button>
          
          <button
            onClick={resetStatus}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
        </div>

        {/* Status Display */}
        {status.isGenerating && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-gray-600">Generating PDF... {status.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${status.progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {status.completed && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <strong>Success:</strong> PDF has been generated and downloaded!
          </div>
        )}

        {status.error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong>Error:</strong> {status.error}
          </div>
        )}
      </div>

      {/* PDF Template Preview */}
      <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">PDF Template Preview</h3>
        <div className="transform scale-50 origin-top-left" style={{ width: '200%', height: '200%' }}>
          <div ref={templateRef}>
            <PDFTemplate reportData={reportData} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFGeneratorExample;