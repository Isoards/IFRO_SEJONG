# Traffic Chart Components

This directory contains chart components for visualizing traffic data in the WILL traffic analysis system.

## Components

### TrafficVolumeBarChart
A bar chart component that displays traffic volume by direction (NS, SN, EW, WE).

**Props:**
- `data: TrafficVolumeData` - Traffic volume data by direction
- `title?: string` - Chart title (optional)
- `onChartReady?: (chartImage: string) => void` - Callback when chart image is ready for PDF
- `className?: string` - Additional CSS classes

**Usage:**
```tsx
import { TrafficVolumeBarChart } from './components/Charts';

const volumeData = {
  NS: 1250,
  SN: 980,
  EW: 1450,
  WE: 1120
};

<TrafficVolumeBarChart 
  data={volumeData}
  title="Traffic Volume by Direction"
  onChartReady={(imageData) => console.log('Chart ready:', imageData)}
/>
```

### TrafficTimeLineChart
A line chart component that shows traffic volume and speed changes over time.

**Props:**
- `data: TrafficData[]` - Array of traffic data points with hour, volume, and speed
- `title?: string` - Chart title (optional)
- `onChartReady?: (chartImage: string) => void` - Callback when chart image is ready for PDF
- `className?: string` - Additional CSS classes
- `showVolume?: boolean` - Whether to show volume line (default: true)
- `showSpeed?: boolean` - Whether to show speed line (default: true)

**Usage:**
```tsx
import { TrafficTimeLineChart } from './components/Charts';

const timeData = [
  { hour: '06:00', volume: 450, speed: 45 },
  { hour: '07:00', volume: 850, speed: 35 },
  // ... more data points
];

<TrafficTimeLineChart 
  data={timeData}
  title="Traffic Variation Over Time"
  showVolume={true}
  showSpeed={true}
/>
```

### TrafficAnalysisChart
A combined chart component that can display traffic data as bars, lines, or both.

**Props:**
- `data: TrafficData[]` - Array of traffic data points
- `title?: string` - Chart title (optional)
- `onChartReady?: (chartImage: string) => void` - Callback when chart image is ready for PDF
- `className?: string` - Additional CSS classes
- `chartType?: 'combined' | 'volume-only' | 'speed-only'` - Chart display type

**Usage:**
```tsx
import { TrafficAnalysisChart } from './components/Charts';

<TrafficAnalysisChart 
  data={timeData}
  title="Traffic Analysis"
  chartType="combined"
/>
```

### ResponsiveTrafficChart
A wrapper component that provides responsive behavior and can render different chart types.

**Props:**
- `volumeData?: TrafficVolumeData` - Volume data (required for bar charts)
- `timeData?: TrafficData[]` - Time series data (required for line/analysis charts)
- `chartType: ChartType` - Type of chart to render ('bar' | 'line' | 'combined' | 'analysis')
- `title?: string` - Chart title (optional)
- `onChartReady?: (chartImage: string) => void` - Callback when chart image is ready for PDF
- `className?: string` - Additional CSS classes
- `responsive?: boolean` - Enable responsive behavior (default: true)

**Usage:**
```tsx
import { ResponsiveTrafficChart } from './components/Charts';

<ResponsiveTrafficChart 
  volumeData={volumeData}
  timeData={timeData}
  chartType="bar"
  title="Responsive Traffic Chart"
  responsive={true}
/>
```

## Features

### Chart Image Generation
All chart components support generating PNG images for PDF inclusion:

```tsx
const handleChartReady = (imageData: string) => {
  // imageData is a base64 encoded PNG image
  // Can be used directly in PDF generation or downloaded
  console.log('Chart image ready:', imageData);
};

<TrafficVolumeBarChart 
  data={volumeData}
  onChartReady={handleChartReady}
/>
```

### Responsive Design
Charts automatically adapt to their container size and provide responsive styling:

- Mobile (< 640px): Smaller text and compact layout
- Tablet (640px - 1024px): Medium text and balanced layout  
- Desktop (> 1024px): Full text and spacious layout

### Styling
Charts use Tailwind CSS classes and can be customized:

- Consistent color scheme across all charts
- Professional styling with proper spacing and typography
- Hover effects and interactive tooltips
- Print-friendly colors for PDF generation

### Accessibility
- Proper color contrast ratios
- Descriptive tooltips and labels
- Keyboard navigation support (via Recharts)
- Screen reader friendly markup

## Dependencies

- **recharts**: Chart rendering library
- **html2canvas**: Chart to image conversion
- **tailwindcss**: Styling framework

## Demo

A demo component is available at `./ChartDemo.tsx` that showcases all chart types with sample data and download functionality.

## Testing

Basic unit tests are provided in `./__tests__/TrafficCharts.test.tsx`. Note that testing chart components requires mocking ResizeObserver and html2canvas APIs.

## Integration with PDF Generation

These chart components are designed to work seamlessly with the PDF report generation system:

1. Charts generate high-quality PNG images via the `onChartReady` callback
2. Images are optimized for PDF inclusion (2x scale, white background)
3. Charts maintain consistent styling when converted to images
4. Error handling ensures graceful fallbacks if image generation fails

## Performance Considerations

- Charts use React.memo for performance optimization
- Image generation is debounced to avoid excessive processing
- Responsive behavior uses ResizeObserver for efficient size detection
- Large datasets are handled efficiently by Recharts' virtualization