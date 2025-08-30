import React, { useRef, useEffect, useState } from 'react';
import { TrafficVolumeBarChart } from './TrafficVolumeBarChart';
import { TrafficTimeLineChart } from './TrafficTimeLineChart';
import { TrafficAnalysisChart } from './TrafficAnalysisChart';
import { TrafficVolumeData, TrafficData } from '../../../shared/types/global.types';

export type ChartType = 'bar' | 'line' | 'combined' | 'analysis';

interface ResponsiveTrafficChartProps {
  volumeData?: TrafficVolumeData;
  timeData?: TrafficData[];
  chartType: ChartType;
  title?: string;
  onChartReady?: (chartImage: string) => void;
  className?: string;
  responsive?: boolean;
  isPDFGenerating?: boolean;
}

export const ResponsiveTrafficChart: React.FC<ResponsiveTrafficChartProps> = ({
  volumeData,
  timeData,
  chartType,
  title,
  onChartReady,
  className = '',
  responsive = true,
  isPDFGenerating = false
}) => {
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle responsive sizing
  useEffect(() => {
    if (!responsive || !containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setContainerSize({ width, height });
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, [responsive]);

  // Determine responsive classes based on container size
  const getResponsiveClasses = () => {
    if (!responsive) return '';
    
    const { width } = containerSize;
    if (width < 640) return 'text-sm'; // Mobile
    if (width < 1024) return 'text-base'; // Tablet
    return 'text-lg'; // Desktop
  };

  const renderChart = () => {
    const responsiveClass = getResponsiveClasses();
    const chartClassName = `w-full ${className}`;

    switch (chartType) {
      case 'bar':
        if (!volumeData || Object.keys(volumeData).length === 0) {
          return <div className="p-4 text-center text-gray-500">No directional data available</div>;
        }
        return (
          <TrafficVolumeBarChart
            data={volumeData}
            title={title}
            onChartReady={onChartReady}
            className={chartClassName}
            isPDFGenerating={isPDFGenerating}
          />
        );

      case 'line':
        if (!timeData || timeData.length === 0) {
          return <div className="p-4 text-center text-gray-500">No time series data available</div>;
        }
        return (
          <TrafficTimeLineChart
            data={timeData}
            title={title}
            onChartReady={onChartReady}
            className={chartClassName}
            isPDFGenerating={isPDFGenerating}
          />
        );

      case 'combined':
      case 'analysis':
        if (!timeData || timeData.length === 0) {
          return <div className="p-4 text-center text-gray-500">No time series data available</div>;
        }
        return (
          <TrafficAnalysisChart
            data={timeData}
            title={title}
            className={chartClassName}
          />
        );

      default:
        return <div className="p-4 text-center text-gray-500">Invalid chart type specified</div>;
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`w-full ${responsive ? 'min-h-0' : ''} ${className}`}
      data-chart-container
    >
      {renderChart()}
    </div>
  );
};