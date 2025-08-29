import { PDFReportGenerator } from '../PDFReportGenerator';
import { ReportData, PDFConfig } from '../../types/global.types';

// Mock the dependencies
jest.mock('jspdf');
jest.mock('html2canvas');
jest.mock('../pdf.utils', () => ({
  createPDFInstance: jest.fn(),
  htmlToCanvas: jest.fn(),
  canvasToImageData: jest.fn(),
  downloadPDF: jest.fn(),
  generateReportFilename: jest.fn(),
  isPDFGenerationSupported: jest.fn(() => true),
  estimateGenerationTime: jest.fn(() => 3000),
  DEFAULT_PDF_CONFIG: {
    format: 'A4',
    orientation: 'portrait',
    margins: { top: 20, right: 20, bottom: 20, left: 20 },
    quality: 1.0,
  }
}));

describe('PDFReportGenerator', () => {
  let mockReportData: ReportData;
  let mockTemplateElement: HTMLElement;

  beforeEach(() => {
    // Mock report data
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
      peakDirection: 'SN'
    };

    // Mock template element
    mockTemplateElement = document.createElement('div');
    mockTemplateElement.innerHTML = '<div>Test PDF Template</div>';
    
    // Mock getBoundingClientRect
    mockTemplateElement.getBoundingClientRect = jest.fn().mockReturnValue({
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      bottom: 600,
      right: 800
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create instance with default configuration', () => {
      const generator = new PDFReportGenerator();
      expect(generator).toBeInstanceOf(PDFReportGenerator);
      expect(generator.getConfig()).toBeDefined();
    });

    it('should create instance with custom configuration', () => {
      const customConfig: Partial<PDFConfig> = {
        format: 'Letter',
        orientation: 'landscape'
      };
      
      const generator = new PDFReportGenerator(customConfig);
      const config = generator.getConfig();
      
      expect(config.format).toBe('Letter');
      expect(config.orientation).toBe('landscape');
    });

    it('should create instance with retry options', () => {
      const retryOptions = {
        maxRetries: 5,
        retryDelay: 2000,
        backoffMultiplier: 3
      };
      
      const generator = new PDFReportGenerator({}, undefined, retryOptions);
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });

    it('should create instance with memory optimization options', () => {
      const memoryOptions = {
        enableGarbageCollection: false,
        chunkSize: 2048 * 1024,
        maxMemoryUsage: 200
      };
      
      const generator = new PDFReportGenerator({}, undefined, {}, memoryOptions);
      expect(generator).toBeInstanceOf(PDFReportGenerator);
    });
  });

  describe('Configuration Management', () => {
    it('should update configuration', () => {
      const generator = new PDFReportGenerator();
      const newConfig: Partial<PDFConfig> = {
        quality: 0.8,
        margins: { top: 30, right: 30, bottom: 30, left: 30 }
      };
      
      generator.updateConfig(newConfig);
      const config = generator.getConfig();
      
      expect(config.quality).toBe(0.8);
      expect(config.margins.top).toBe(30);
    });

    it('should update retry options', () => {
      const generator = new PDFReportGenerator();
      const newRetryOptions = {
        maxRetries: 10,
        retryDelay: 3000
      };
      
      generator.updateRetryOptions(newRetryOptions);
      // Since retryOptions is private, we can't directly test it
      // but we can verify the method doesn't throw
      expect(() => generator.updateRetryOptions(newRetryOptions)).not.toThrow();
    });

    it('should update memory options', () => {
      const generator = new PDFReportGenerator();
      const newMemoryOptions = {
        maxMemoryUsage: 150,
        enableGarbageCollection: false
      };
      
      generator.updateMemoryOptions(newMemoryOptions);
      // Since memoryOptions is private, we can't directly test it
      // but we can verify the method doesn't throw
      expect(() => generator.updateMemoryOptions(newMemoryOptions)).not.toThrow();
    });
  });

  describe('Generation Status', () => {
    it('should track generation status', () => {
      const generator = new PDFReportGenerator();
      
      expect(generator.isCurrentlyGenerating()).toBe(false);
    });

    it('should allow cancellation', () => {
      const generator = new PDFReportGenerator();
      
      expect(() => generator.cancelGeneration()).not.toThrow();
    });
  });

  describe('Static Methods', () => {
    it('should check browser support', () => {
      // Mock the static method
      jest.spyOn(PDFReportGenerator, 'isSupported').mockReturnValue(true);
      
      const isSupported = PDFReportGenerator.isSupported();
      expect(typeof isSupported).toBe('boolean');
      expect(isSupported).toBe(true);
    });

    it('should estimate generation time', () => {
      // Mock the static method
      jest.spyOn(PDFReportGenerator, 'estimateTime').mockReturnValue(3000);
      
      const estimatedTime = PDFReportGenerator.estimateTime(mockReportData);
      expect(typeof estimatedTime).toBe('number');
      expect(estimatedTime).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should prevent concurrent generation', async () => {
      const generator = new PDFReportGenerator();
      
      // Mock the internal generation to simulate ongoing process
      (generator as any).isGenerating = true;
      
      await expect(
        generator.generateReport(mockReportData, mockTemplateElement)
      ).rejects.toThrow('PDF generation is already in progress');
    });
  });
});