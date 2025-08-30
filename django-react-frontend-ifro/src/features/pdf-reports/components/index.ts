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
export { PDFReportGenerator } from '../../../shared/utils/PDFReportGenerator';
export { usePDFGeneration } from '../../../shared/utils/usePDFGeneration';
export * from '../../../shared/utils/pdf.utils';

// PDF Types (re-exported from global types)
export type {
  PDFConfig,
  ReportData,
  TrafficVolumeData,
  PDFGenerationStatus,
  AITrafficAnalysis,
  AIAnalysisResponse,
  EnhancedReportData,
} from '../../../shared/types/global.types';