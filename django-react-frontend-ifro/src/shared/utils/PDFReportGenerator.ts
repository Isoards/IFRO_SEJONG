import jsPDF from 'jspdf';
import { debugLog } from "./debugUtils";
import { ReportData, PDFConfig, PDFGenerationStatus } from '../types/global.types';
import {
  createPDFInstance,
  htmlToCanvas,
  canvasToImageData,
  downloadPDF,
  generateReportFilename,
  isPDFGenerationSupported,
  estimateGenerationTime,
  DEFAULT_PDF_CONFIG,
} from './pdf.utils';

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

export class PDFReportGenerator {
  private config: PDFConfig;
  private onProgress?: (status: PDFGenerationStatus) => void;
  private retryOptions: RetryOptions;
  private memoryOptions: MemoryOptimizationOptions;

  private isGenerating: boolean = false;

  constructor(
    config: Partial<PDFConfig> = {}, 
    onProgress?: (status: PDFGenerationStatus) => void,
    retryOptions: Partial<RetryOptions> = {},
    memoryOptions: Partial<MemoryOptimizationOptions> = {}
  ) {
    this.config = { ...DEFAULT_PDF_CONFIG, ...config };
    this.onProgress = onProgress;
    this.retryOptions = {
      maxRetries: 3,
      retryDelay: 1000,
      backoffMultiplier: 2,
      ...retryOptions
    };
    this.memoryOptions = {
      enableGarbageCollection: true,
      chunkSize: 1024 * 1024, // 1MB chunks
      maxMemoryUsage: 200, // 200MB max (increased limit)
      ...memoryOptions
    };
  }

  /**
   * Generates a PDF report from the provided data with retry logic
   */
  async generateReport(reportData: ReportData, templateElement: HTMLElement): Promise<void> {
    if (this.isGenerating) {
      throw new Error('PDF generation is already in progress');
    }

    if (!isPDFGenerationSupported()) {
      throw new Error('PDF generation is not supported in this browser');
    }

    this.isGenerating = true;

    try {
      await this.executeWithRetry(async () => {
        await this.generateReportInternal(reportData, templateElement);
      });
    } finally {
      this.isGenerating = false;
    }
  }

  /**
   * Internal method for PDF generation with simplified error handling
   */
  private async generateReportInternal(reportData: ReportData, templateElement: HTMLElement): Promise<void> {
    let currentProgress = 0;
    let canvas: HTMLCanvasElement | null = null;
    let pdf: jsPDF | null = null;

    try {
      // Update progress: Starting
      this.updateProgress({
        isGenerating: true,
        progress: 0,
        error: null,
        completed: false,
      });

      // Step 1: Create PDF instance
      pdf = createPDFInstance(this.config);
      currentProgress = 10;
      this.updateProgress({
        isGenerating: true,
        progress: currentProgress,
        error: null,
        completed: false,
      });

      // Step 2: Convert HTML template to canvas with higher quality
      canvas = await htmlToCanvas(templateElement, {
        scale: 1.5, // Good balance between quality and performance
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
      });
      currentProgress = 50;
      this.updateProgress({
        isGenerating: true,
        progress: currentProgress,
        error: null,
        completed: false,
      });

      // Step 3: Convert canvas to image data with validation
      let imageData: string;
      try {
        imageData = canvasToImageData(canvas, 'PNG', 0.8);
        
        // Validate image data
        if (!imageData || !imageData.startsWith('data:image/')) {
          throw new Error('Invalid image data generated');
        }
        
        // Check if image data is not just a header
        if (imageData.length < 100) {
          throw new Error('Image data too short, likely corrupt');
        }
        
        debugLog('Successfully generated image data, length:', imageData.length);
        
      } catch (error) {
        console.warn('Failed to generate image data, using fallback:', error);
        // Create a simple fallback canvas with text
        const fallbackCanvas = document.createElement('canvas');
        fallbackCanvas.width = 800;
        fallbackCanvas.height = 600;
        const ctx = fallbackCanvas.getContext('2d');
        if (ctx) {
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, 800, 600);
          ctx.fillStyle = '#333333';
          ctx.font = '24px Arial';
          ctx.textAlign = 'center';
          ctx.fillText('Chart data not available', 400, 300);
          ctx.fillText('PDF generated on ' + new Date().toLocaleDateString(), 400, 350);
        }
        imageData = fallbackCanvas.toDataURL('image/png', 0.8);
      }
      
      currentProgress = 70;
      this.updateProgress({
        isGenerating: true,
        progress: currentProgress,
        error: null,
        completed: false,
      });

      // Step 4: Add image to PDF with automatic page breaks
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      // Use minimal margins
      const marginX = 10; // 10mm margin
      const marginY = 10; // 10mm margin
      const marginRight = 10;
      const marginBottom = 10;
      
      const availableWidth = pdfWidth - marginX - marginRight;
      const availableHeight = pdfHeight - marginY - marginBottom;

      // Validate canvas dimensions
      const canvasWidth = canvas.width || 1;
      const canvasHeight = canvas.height || 1;
      const canvasAspectRatio = canvasWidth / canvasHeight;
      
      debugLog('PDF dimensions:', { pdfWidth, pdfHeight });
      debugLog('Canvas dimensions:', { canvasWidth, canvasHeight });
      debugLog('Canvas aspect ratio:', canvasAspectRatio);

      // Calculate image dimensions maintaining aspect ratio
      const imgWidth = availableWidth;
      const imgHeight = imgWidth / canvasAspectRatio;
      
      debugLog('Calculated image size:', { imgWidth, imgHeight });
      debugLog('Available height per page:', availableHeight);

      // Check if content fits in one page
      if (imgHeight <= availableHeight) {
        // Content fits in one page
        debugLog('Content fits in one page');
        pdf.addImage(imageData, 'PNG', marginX, marginY, imgWidth, imgHeight);
      } else {
        // Content needs multiple pages - clean split without overlap
        debugLog('Content needs multiple pages');
        
        const pagesNeeded = Math.ceil(imgHeight / availableHeight);
        debugLog('Pages needed:', pagesNeeded);
        
        for (let pageIndex = 0; pageIndex < pagesNeeded; pageIndex++) {
          if (pageIndex > 0) {
            pdf.addPage(); // Add new page
            debugLog(`Added page ${pageIndex + 1}`);
          }
          
          // Calculate the portion of the image for this page (clean split)
          const sourceY = pageIndex * availableHeight * (canvasHeight / imgHeight);
          const remainingCanvasHeight = canvasHeight - sourceY;
          const sourceHeight = Math.min(availableHeight * (canvasHeight / imgHeight), remainingCanvasHeight);
          const displayHeight = sourceHeight * (imgHeight / canvasHeight);
          
          debugLog(`Page ${pageIndex + 1}:`, { 
            sourceY: Math.round(sourceY), 
            sourceHeight: Math.round(sourceHeight), 
            displayHeight: Math.round(displayHeight),
            remainingCanvasHeight: Math.round(remainingCanvasHeight)
          });
          
          // Create a temporary canvas for this page portion
          const tempCanvas = document.createElement('canvas');
          tempCanvas.width = canvasWidth;
          tempCanvas.height = Math.round(sourceHeight);
          const tempCtx = tempCanvas.getContext('2d');
          
          if (tempCtx && sourceHeight > 0) {
            // Draw the portion of the original canvas
            tempCtx.drawImage(
              canvas, 
              0, Math.round(sourceY), canvasWidth, Math.round(sourceHeight), // source
              0, 0, canvasWidth, Math.round(sourceHeight) // destination
            );
            
            // Convert to image data
            const pageImageData = tempCanvas.toDataURL('image/PNG', 0.8);
            
            // Add to PDF
            pdf.addImage(pageImageData, 'PNG', marginX, marginY, imgWidth, displayHeight);
          }
        }
      }
      
      currentProgress = 90;
      this.updateProgress({
        isGenerating: true,
        progress: currentProgress,
        error: null,
        completed: false,
      });

      // Step 5: Download the PDF
      const filename = generateReportFilename(reportData);
      downloadPDF(pdf, filename);
      
      // Complete
      this.updateProgress({
        isGenerating: false,
        progress: 100,
        error: null,
        completed: true,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      this.updateProgress({
        isGenerating: false,
        progress: currentProgress,
        error: errorMessage,
        completed: false,
      });
      throw error;
    } finally {
      // Clean up resources
      if (canvas) {
        try {
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
          }
        } catch (e) {
          console.warn('Failed to cleanup canvas:', e);
        }
      }
      pdf = null;
    }
  }

  /**
   * Generates a preview of the PDF (returns base64 data URL)
   */
  async generatePreview(reportData: ReportData, templateElement: HTMLElement): Promise<string> {
    if (!isPDFGenerationSupported()) {
      throw new Error('PDF generation is not supported in this browser');
    }

    try {
      const pdf = createPDFInstance(this.config);
      const canvas = await htmlToCanvas(templateElement, {
        scale: 0.5, // Lower quality for preview
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
      });

      const imageData = canvasToImageData(canvas, 'PNG', 0.7);
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const marginX = this.config.margins.left;
      const marginY = this.config.margins.top;
      const availableWidth = pdfWidth - this.config.margins.left - this.config.margins.right;
      const availableHeight = pdfHeight - this.config.margins.top - this.config.margins.bottom;

      const canvasAspectRatio = canvas.width / canvas.height;
      const availableAspectRatio = availableWidth / availableHeight;

      let imgWidth, imgHeight;
      if (canvasAspectRatio > availableAspectRatio) {
        imgWidth = availableWidth;
        imgHeight = availableWidth / canvasAspectRatio;
      } else {
        imgHeight = availableHeight;
        imgWidth = availableHeight * canvasAspectRatio;
      }

      const imgX = marginX + (availableWidth - imgWidth) / 2;
      const imgY = marginY + (availableHeight - imgHeight) / 2;

      pdf.addImage(imageData, 'PNG', imgX, imgY, imgWidth, imgHeight);
      
      return pdf.output('datauristring');
    } catch (error) {
      throw new Error(`Failed to generate PDF preview: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Updates the configuration
   */
  updateConfig(newConfig: Partial<PDFConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Gets the current configuration
   */
  getConfig(): PDFConfig {
    return { ...this.config };
  }

  /**
   * Updates progress callback
   */
  private updateProgress(status: PDFGenerationStatus): void {
    if (this.onProgress) {
      this.onProgress(status);
    }
  }

  /**
   * Static method to check browser compatibility
   */
  static isSupported(): boolean {
    return isPDFGenerationSupported();
  }

  /**
   * Static method to estimate generation time
   */
  static estimateTime(reportData: ReportData): number {
    return estimateGenerationTime(reportData);
  }

  /**
   * Executes a function with retry logic
   */
  private async executeWithRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= this.retryOptions.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt === this.retryOptions.maxRetries) {
          break;
        }

        // Check if error is retryable
        if (!this.isRetryableError(lastError)) {
          throw lastError;
        }

        // Calculate delay with exponential backoff
        const delay = this.retryOptions.retryDelay * Math.pow(this.retryOptions.backoffMultiplier, attempt);
        
        console.warn(`PDF generation attempt ${attempt + 1} failed, retrying in ${delay}ms:`, lastError.message);
        
        await this.sleep(delay);
      }
    }
    
    throw new Error(`PDF generation failed after ${this.retryOptions.maxRetries + 1} attempts. Last error: ${lastError?.message}`);
  }

  /**
   * Checks if an error is retryable
   */
  private isRetryableError(error: Error): boolean {
    // Never retry if generation was aborted or cancelled
    if (error.message.includes('aborted') || error.message.includes('cancelled')) {
      return false;
    }
    
    const retryableErrors = [
      'Network error',
      'Timeout',
      'Canvas rendering failed',
      'Memory allocation failed',
      'Temporary resource unavailable'
    ];
    
    return retryableErrors.some(retryableError => 
      error.message.toLowerCase().includes(retryableError.toLowerCase())
    );
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }



  /**
   * Cancels the current PDF generation
   */
  public cancelGeneration(): void {
    // For now, we just update the status since we removed abort controller
    this.updateProgress({
      isGenerating: false,
      progress: 0,
      error: 'PDF generation was cancelled',
      completed: false,
    });
  }

  /**
   * Gets current generation status
   */
  public isCurrentlyGenerating(): boolean {
    return this.isGenerating;
  }

  /**
   * Updates retry options
   */
  public updateRetryOptions(options: Partial<RetryOptions>): void {
    this.retryOptions = { ...this.retryOptions, ...options };
  }

  /**
   * Updates memory optimization options
   */
  public updateMemoryOptions(options: Partial<MemoryOptimizationOptions>): void {
    this.memoryOptions = { ...this.memoryOptions, ...options };
  }
}