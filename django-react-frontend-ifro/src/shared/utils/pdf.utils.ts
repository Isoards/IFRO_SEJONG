import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { PDFConfig, ReportData } from '../types/global.types';

// Default PDF configuration
export const DEFAULT_PDF_CONFIG: PDFConfig = {
  format: 'A4',
  orientation: 'portrait',
  margins: {
    top: 20,
    right: 20,
    bottom: 20,
    left: 20,
  },
  quality: 1.0,
};

/**
 * Creates a new jsPDF instance with the specified configuration
 */
export const createPDFInstance = (config: Partial<PDFConfig> = {}): jsPDF => {
  const finalConfig = { ...DEFAULT_PDF_CONFIG, ...config };
  
  return new jsPDF({
    orientation: finalConfig.orientation,
    unit: 'mm',
    format: finalConfig.format.toLowerCase() as 'a4' | 'letter',
  });
};

/**
 * Converts an HTML element to canvas using html2canvas
 */
export const htmlToCanvas = async (
  element: HTMLElement,
  options: Partial<{
    scale: number;
    useCORS: boolean;
    allowTaint: boolean;
    backgroundColor: string;
  }> = {}
): Promise<HTMLCanvasElement> => {
  const defaultOptions = {
    scale: 2,
    useCORS: true,
    allowTaint: true,
    backgroundColor: '#ffffff',
    ...options,
  };

  return await html2canvas(element, defaultOptions);
};

/**
 * Converts canvas to image data URL
 */
export const canvasToImageData = (
  canvas: HTMLCanvasElement,
  format: 'PNG' | 'JPEG' = 'PNG',
  quality: number = 1.0
): string => {
  return canvas.toDataURL(`image/${format.toLowerCase()}`, quality);
};

/**
 * Adds an image to PDF with automatic scaling and positioning
 */
export const addImageToPDF = (
  pdf: jsPDF,
  imageData: string,
  x: number,
  y: number,
  maxWidth: number,
  maxHeight: number
): { width: number; height: number } => {
  // Create a temporary image to get dimensions
  const img = new Image();
  img.src = imageData;
  
  const imgWidth = img.width;
  const imgHeight = img.height;
  
  // Calculate scaling to fit within max dimensions
  const scaleX = maxWidth / imgWidth;
  const scaleY = maxHeight / imgHeight;
  const scale = Math.min(scaleX, scaleY);
  
  const finalWidth = imgWidth * scale;
  const finalHeight = imgHeight * scale;
  
  pdf.addImage(imageData, 'PNG', x, y, finalWidth, finalHeight);
  
  return { width: finalWidth, height: finalHeight };
};

/**
 * Adds text with automatic line wrapping
 */
export const addWrappedText = (
  pdf: jsPDF,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number = 7
): number => {
  const lines = pdf.splitTextToSize(text, maxWidth);
  pdf.text(lines, x, y);
  return y + (lines.length * lineHeight);
};

/**
 * Downloads the PDF file
 */
export const downloadPDF = (pdf: jsPDF, filename: string): void => {
  pdf.save(filename);
};

/**
 * Saves PDF to server and triggers automatic embedding
 */
export const savePDFToServer = async (pdf: jsPDF, filename: string): Promise<boolean> => {
  try {
    // Convert PDF to base64
    const pdfData = pdf.output('datauristring');
    const base64Data = pdfData.split(',')[1]; // Remove data:application/pdf;filename=generated.pdf;base64, prefix
    
    // Send to backend
    const response = await fetch('http://localhost:8000/api/traffic/pdf/save-and-notify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: filename,
        pdf_data: base64Data
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('PDF 서버 저장 및 자동 임베딩 완료:', result.message);
      return true;
    } else {
      console.error('PDF 서버 저장 실패:', response.statusText);
      return false;
    }
  } catch (error) {
    console.error('PDF 서버 저장 오류:', error);
    return false;
  }
};

/**
 * Downloads PDF and saves to server for automatic embedding
 */
export const downloadAndSavePDF = async (pdf: jsPDF, filename: string): Promise<void> => {
  // Download to user's device
  downloadPDF(pdf, filename);
  
  // Save to server for automatic embedding
  const saved = await savePDFToServer(pdf, filename);
  
  if (saved) {
    console.log('PDF가 다운로드되고 챗봇에 자동 임베딩되었습니다!');
  } else {
    console.warn('PDF 다운로드는 완료되었지만 서버 저장에 실패했습니다.');
  }
};

/**
 * Generates a filename for the PDF report
 */
export const generateReportFilename = (reportData: ReportData): string => {
  const date = new Date(reportData.datetime);
  const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD format
  const intersectionName = reportData.intersection.name
    .replace(/[^a-zA-Z0-9]/g, '_')
    .toLowerCase();
  
  return `traffic_report_${intersectionName}_${dateStr}.pdf`;
};

/**
 * Validates if the browser supports PDF generation
 */
export const isPDFGenerationSupported = (): boolean => {
  try {
    // Check if required APIs are available
    return !!(
      window.HTMLCanvasElement &&
      window.CanvasRenderingContext2D &&
      document.createElement('canvas').getContext('2d')
    );
  } catch (error) {
    return false;
  }
};

/**
 * Estimates PDF generation time based on content complexity
 */
export const estimateGenerationTime = (reportData: ReportData): number => {
  // Base time in milliseconds
  let estimatedTime = 2000;
  
  // Add time for charts
  if (reportData.chartData && reportData.chartData.length > 0) {
    estimatedTime += 1500;
  }
  
  // Add time for interpretation text
  if (reportData.interpretation) {
    estimatedTime += 500;
  }
  
  return estimatedTime;
};