// PDF Components
export { PDFTemplate } from './PDFTemplate';
export { default as PDFGeneratorExample } from './PDFGeneratorExample';
export { default as EnhancedPDFGenerator } from './EnhancedPDFGenerator';

// Export section components
export {
  ReportHeader,
  IntersectionInfo,
  TrafficDataTable,
  InterpretationSection,
  ChartSection,
  ReportFooter,
} from './sections';

// PDF Utilities
export { PDFReportGenerator } from '../../utils/PDFReportGenerator';
export { usePDFGeneration } from '../../utils/usePDFGeneration';
export * from '../../utils/pdf.utils';

// PDF Types (re-exported from global types)
export type {
  PDFConfig,
  ReportData,
  TrafficVolumeData,
  PDFGenerationStatus,
  AITrafficAnalysis,
  AIAnalysisResponse,
  EnhancedReportData,
} from '../../types/global.types';