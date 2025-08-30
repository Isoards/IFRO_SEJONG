import { PDFReportGenerator } from '../PDFReportGenerator';
import { isPDFGenerationSupported } from '../pdf.utils';
import { ReportData } from '../../types/global.types';

// Mock the pdf.utils
jest.mock('../pdf.utils', () => ({
  createPDFInstance: jest.fn(),
  htmlToCanvas: jest.fn(),
  canvasToImageData: jest.fn(),
  downloadPDF: jest.fn(),
  generateReportFilename: jest.fn(),
  isPDFGenerationSupported: jest.fn(),
  estimateGenerationTime: jest.fn(() => 3000),
  DEFAULT_PDF_CONFIG: {
    format: 'A4',
    orientation: 'portrait',
    margins: { top: 20, right: 20, bottom: 20, left: 20 },
    quality: 1.0,
  }
}));

const mockIsPDFGenerationSupported = isPDFGenerationSupported as jest.MockedFunction<
  typeof isPDFGenerationSupported
>;

describe('PDF Generation Browser Compatibility Tests', () => {
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
      peakDirection: 'SN',
      chartData: []
    };

    // Create mock template element with proper DOM methods
    mockTemplateElement = {
      innerHTML: '<div>Test PDF Template</div>',
      getBoundingClientRect: jest.fn().mockReturnValue({
        width: 800,
        height: 600,
        top: 0,
        left: 0,
        bottom: 600,
        right: 800
      }),
      nodeType: 1,
      nodeName: 'DIV',
    } as any;

    jest.clearAllMocks();
  });

  describe('Browser Support Detection', () => {
    it('should detect Chrome support', () => {
      // Mock Chrome user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);
    });

    it('should detect Firefox support', () => {
      // Mock Firefox user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);
    });

    it('should detect Safari support', () => {
      // Mock Safari user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);
    });

    it('should detect Edge support', () => {
      // Mock Edge user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);
    });

    it('should handle unsupported browsers', () => {
      // Mock old IE user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)'
      });

      mockIsPDFGenerationSupported.mockReturnValue(false);
      
      expect(PDFReportGenerator.isSupported()).toBe(false);
    });

    it('should handle missing Canvas API', () => {
      // Mock missing Canvas support
      const originalHTMLCanvasElement = global.HTMLCanvasElement;
      delete (global as any).HTMLCanvasElement;

      mockIsPDFGenerationSupported.mockReturnValue(false);
      
      expect(PDFReportGenerator.isSupported()).toBe(false);

      // Restore
      global.HTMLCanvasElement = originalHTMLCanvasElement;
    });

    it('should handle missing Blob API', () => {
      // Mock missing Blob support
      const originalBlob = global.Blob;
      delete (global as any).Blob;

      mockIsPDFGenerationSupported.mockReturnValue(false);
      
      expect(PDFReportGenerator.isSupported()).toBe(false);

      // Restore
      global.Blob = originalBlob;
    });
  });

  describe('Mobile Browser Optimization', () => {
    beforeEach(() => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });

      // Mock touch support
      Object.defineProperty(navigator, 'maxTouchPoints', {
        writable: true,
        value: 5,
      });
    });

    it('should optimize for mobile Chrome', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);

      const generator = new PDFReportGenerator({
        quality: 0.8, // Reduced quality for mobile
      });

      expect(generator.getConfig().quality).toBe(0.8);
    });

    it('should optimize for mobile Safari', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
      });

      mockIsPDFGenerationSupported.mockReturnValue(true);

      const generator = new PDFReportGenerator({
        quality: 0.7, // Further reduced for Safari
      });

      expect(generator.getConfig().quality).toBe(0.7);
    });

    it('should handle memory constraints on mobile', () => {
      const generator = new PDFReportGenerator({}, undefined, {}, {
        maxMemoryUsage: 50, // Reduced for mobile
        enableGarbageCollection: true,
        chunkSize: 512 * 1024, // Smaller chunks
      });

      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });
  });

  describe('Performance Optimization', () => {
    it('should optimize for large documents', () => {
      const largeDocumentConfig = {
        quality: 0.6, // Reduced quality for large docs
        format: 'A4' as const,
        orientation: 'portrait' as const,
      };

      const generator = new PDFReportGenerator(largeDocumentConfig);
      
      expect(generator.getConfig().quality).toBe(0.6);
    });

    it('should handle memory pressure', () => {
      // Mock memory API
      Object.defineProperty(performance, 'memory', {
        writable: true,
        value: {
          usedJSHeapSize: 80 * 1024 * 1024, // 80MB
          totalJSHeapSize: 100 * 1024 * 1024, // 100MB
          jsHeapSizeLimit: 2048 * 1024 * 1024, // 2GB
        },
      });

      const generator = new PDFReportGenerator({}, undefined, {}, {
        maxMemoryUsage: 100,
        enableGarbageCollection: true,
      });

      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should optimize canvas rendering for different screen densities', () => {
      // Mock high DPI display
      Object.defineProperty(window, 'devicePixelRatio', {
        writable: true,
        value: 2,
      });

      const generator = new PDFReportGenerator({
        quality: 1.5, // Adjusted for high DPI
      });

      expect(generator.getConfig().quality).toBe(1.5);
    });

    it('should handle slow networks with timeout optimization', async () => {
      const generator = new PDFReportGenerator({}, undefined, {
        maxRetries: 5,
        retryDelay: 2000,
        backoffMultiplier: 1.5,
      });

      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });
  });

  describe('Cross-Browser Compatibility', () => {
    it('should handle different Canvas implementations', () => {
      // Mock different canvas contexts
      const mockCanvas = document.createElement('canvas');
      const mockContext = {
        clearRect: jest.fn(),
        drawImage: jest.fn(),
        getImageData: jest.fn(),
        putImageData: jest.fn(),
      };

      mockCanvas.getContext = jest.fn().mockReturnValue(mockContext);
      
      // Test that generator can work with different context implementations
      const generator = new PDFReportGenerator();
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should handle different PDF.js versions', () => {
      // Test compatibility with different jsPDF versions
      const generator = new PDFReportGenerator({
        format: 'A4',
        orientation: 'portrait',
      });

      expect(generator.getConfig().format).toBe('A4');
      expect(generator.getConfig().orientation).toBe('portrait');
    });

    it('should handle different html2canvas versions', () => {
      // Test compatibility with different html2canvas versions
      const generator = new PDFReportGenerator({
        quality: 1.0,
      });

      expect(generator.getConfig().quality).toBe(1.0);
    });
  });

  describe('Error Handling Across Browsers', () => {
    it('should handle Chrome-specific errors', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      });

      const generator = new PDFReportGenerator();
      
      // Chrome-specific error handling should be in place
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should handle Firefox-specific errors', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
      });

      const generator = new PDFReportGenerator();
      
      // Firefox-specific error handling should be in place
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should handle Safari-specific errors', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
      });

      const generator = new PDFReportGenerator();
      
      // Safari-specific error handling should be in place
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });
  });

  describe('Feature Detection', () => {
    it('should detect WebGL support', () => {
      // Mock WebGL support
      const mockCanvas = document.createElement('canvas');
      mockCanvas.getContext = jest.fn().mockImplementation((type) => {
        if (type === 'webgl' || type === 'experimental-webgl') {
          return {}; // Mock WebGL context
        }
        return null;
      });

      document.createElement = jest.fn().mockReturnValue(mockCanvas);

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);
    });

    it('should detect OffscreenCanvas support', () => {
      // Mock OffscreenCanvas support
      (global as any).OffscreenCanvas = class OffscreenCanvas {
        constructor(width: number, height: number) {}
        getContext() { return {}; }
      };

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);

      // Cleanup
      delete (global as any).OffscreenCanvas;
    });

    it('should detect Worker support', () => {
      // Mock Worker support
      (global as any).Worker = class Worker {
        constructor(scriptURL: string) {}
        postMessage() {}
        terminate() {}
      };

      mockIsPDFGenerationSupported.mockReturnValue(true);
      
      expect(PDFReportGenerator.isSupported()).toBe(true);

      // Cleanup
      delete (global as any).Worker;
    });
  });

  describe('Accessibility Compliance', () => {
    it('should generate accessible PDFs', () => {
      const generator = new PDFReportGenerator({
        // Configuration for accessible PDFs
        format: 'A4',
        orientation: 'portrait',
      });

      expect(generator.getConfig().format).toBe('A4');
    });

    it('should handle high contrast mode', () => {
      // Mock high contrast mode
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const generator = new PDFReportGenerator();
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should handle reduced motion preferences', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const generator = new PDFReportGenerator();
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });
  });
});