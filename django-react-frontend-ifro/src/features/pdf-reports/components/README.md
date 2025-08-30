# PDF Report Generation with AI Analysis

This module provides comprehensive PDF report generation functionality for the WILL traffic analysis system, enhanced with AI-powered traffic analysis using Google's Gemini API.

## Features

- **PDF Generation**: Convert HTML templates to PDF using jsPDF and html2canvas
- **AI-Enhanced Analysis**: Intelligent traffic analysis using Google Gemini API
- **Customizable Templates**: Flexible PDF template structure with traffic data visualization
- **Progress Tracking**: Real-time progress updates during PDF generation
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Browser Compatibility**: Automatic detection of PDF generation support
- **TypeScript Support**: Full TypeScript definitions for all components and utilities
- **Multi-language Support**: Spanish and Korean translations for AI analysis results

## Installation

The required dependencies are already installed:
- `jspdf`: PDF generation library
- `html2canvas`: HTML to canvas conversion
- `@types/jspdf`: TypeScript definitions
- `axios`: HTTP client for API communication
- `react-i18next`: Internationalization support

## Backend Setup

1. Add your Gemini API key to the backend `.env` file:
```env
GEMINI_API_KEY=your-gemini-api-key-here
```

2. Install the `requests` library in your Django backend:
```bash
pip install requests
```

3. The Gemini service and API endpoints are automatically configured.

## Components

### PDFTemplate
Main template component that renders the PDF content structure with optional AI analysis.

```tsx
import { PDFTemplate } from './components/PDF';

<PDFTemplate 
  reportData={reportData} 
  chartImage={chartImageUrl}
  aiAnalysis={aiAnalysisData}
/>
```

### EnhancedPDFGenerator
Advanced PDF generator with AI analysis integration.

```tsx
import { EnhancedPDFGenerator } from './components/PDF';

<EnhancedPDFGenerator 
  reportData={reportData}
  includeAIAnalysis={true}
  timePeriod="24h"
/>
```

### AIEnhancedPDFButton
Simple button component for generating AI-enhanced PDF reports.

```tsx
import { AIEnhancedPDFButton } from './components/Dashboard';

<AIEnhancedPDFButton 
  reportData={reportData}
  timePeriod="7d"
  buttonText="Download AI Report"
/>
```

### PDFGeneratorExample
Example component demonstrating basic PDF generation functionality.

```tsx
import { PDFGeneratorExample } from './components/PDF';

<PDFGeneratorExample reportData={reportData} />
```

## Utilities

### PDFReportGenerator
Main class for PDF generation with progress tracking.

```tsx
import { PDFReportGenerator } from './components/PDF';

const generator = new PDFReportGenerator(config, onProgress);
await generator.generateReport(reportData, templateElement);
```

### usePDFGeneration Hook
React hook for managing PDF generation state.

```tsx
import { usePDFGeneration } from './components/PDF';

const { status, generatePDF, generatePreview } = usePDFGeneration({
  config: { format: 'A4', orientation: 'portrait' },
  onSuccess: () => console.log('PDF generated!'),
  onError: (error) => console.error(error),
});
```

## Configuration

### PDFConfig Type
```typescript
type PDFConfig = {
  format: 'A4' | 'Letter';
  orientation: 'portrait' | 'landscape';
  margins: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  quality: number;
};
```

### Default Configuration
```typescript
const DEFAULT_PDF_CONFIG: PDFConfig = {
  format: 'A4',
  orientation: 'portrait',
  margins: { top: 20, right: 20, bottom: 20, left: 20 },
  quality: 1.0,
};
```

## Usage Examples

### Basic PDF Generation
```tsx
import React, { useRef } from 'react';
import { PDFTemplate, usePDFGeneration } from './components/PDF';

const MyComponent = ({ reportData }) => {
  const templateRef = useRef<HTMLDivElement>(null);
  
  const { status, generatePDF } = usePDFGeneration({
    onSuccess: () => alert('PDF downloaded!'),
    onError: (error) => alert(`Error: ${error}`),
  });

  const handleDownload = async () => {
    if (templateRef.current) {
      await generatePDF(reportData, templateRef.current);
    }
  };

  return (
    <div>
      <button onClick={handleDownload} disabled={status.isGenerating}>
        {status.isGenerating ? `Generating... ${status.progress}%` : 'Download PDF'}
      </button>
      
      <div ref={templateRef} style={{ position: 'absolute', left: '-9999px' }}>
        <PDFTemplate reportData={reportData} />
      </div>
    </div>
  );
};
```

### AI-Enhanced PDF Generation
```tsx
import React from 'react';
import { AIEnhancedPDFButton } from './components/Dashboard';

const TrafficDashboard = ({ reportData }) => {
  return (
    <div className="dashboard">
      <h1>Traffic Analysis Dashboard</h1>
      
      {/* Simple AI-enhanced PDF button */}
      <AIEnhancedPDFButton 
        reportData={reportData}
        timePeriod="24h"
        buttonText="Download AI Analysis Report"
      />
      
      {/* Or use the full enhanced generator */}
      <EnhancedPDFGenerator 
        reportData={reportData}
        includeAIAnalysis={true}
        timePeriod="7d"
      />
    </div>
  );
};
```

### Manual AI Analysis Integration
```tsx
import React, { useState } from 'react';
import { generateAITrafficAnalysis } from './api/intersections';
import { PDFTemplate } from './components/PDF';

const ManualAIIntegration = ({ reportData }) => {
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAIAnalysis = async () => {
    setLoading(true);
    try {
      const response = await generateAITrafficAnalysis(
        reportData.intersection.id, 
        "24h"
      );
      setAiAnalysis(response.analysis);
    } catch (error) {
      console.error('AI Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={loadAIAnalysis} disabled={loading}>
        {loading ? 'Loading AI Analysis...' : 'Load AI Analysis'}
      </button>
      
      {aiAnalysis && (
        <PDFTemplate 
          reportData={reportData} 
          aiAnalysis={aiAnalysis}
        />
      )}
    </div>
  );
};
```

## File Structure

```
src/components/PDF/
├── index.ts                 # Main exports
├── PDFTemplate.tsx          # PDF template component
├── PDFGeneratorExample.tsx  # Example implementation
└── README.md               # This documentation

src/utils/
├── PDFReportGenerator.ts   # Main PDF generator class
├── pdf.utils.ts           # PDF utility functions
└── usePDFGeneration.ts    # React hook for PDF generation

src/types/
└── global.types.ts        # TypeScript definitions (updated)
```

## Browser Support

The PDF generation functionality automatically detects browser compatibility. It requires:
- HTML5 Canvas support
- Canvas 2D rendering context
- File download capabilities

## Error Handling

The system provides comprehensive error handling for:
- Browser compatibility issues
- PDF generation failures
- Network errors
- Invalid data scenarios

All errors are captured and presented with user-friendly messages.