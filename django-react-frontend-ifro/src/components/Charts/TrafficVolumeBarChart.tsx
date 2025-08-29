import React, { useRef, useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';
import html2canvas from 'html2canvas';
import { TrafficVolumeData } from '../../types/global.types';

interface TrafficVolumeBarChartProps {
  data: TrafficVolumeData;
  title?: string;
  onChartReady?: (chartImage: string) => void;
  className?: string;
  isPDFGenerating?: boolean;
}

interface ChartDataPoint {
  direction: string;
  volume: number;
  label: string;
}

const DIRECTION_LABELS = {
  N: 'Norte',
  S: 'Sur', 
  E: 'Este',
  W: 'Oeste'
};

const CHART_COLORS = {
  N: '#3b82f6', // blue-500
  S: '#10b981', // emerald-500
  E: '#f59e0b', // amber-500
  W: '#ef4444'  // red-500
};

export const TrafficVolumeBarChart: React.FC<TrafficVolumeBarChartProps> = ({
  data,
  title = 'Volumen de Tráfico por Dirección',
  onChartReady,
  className = '',
  isPDFGenerating = false
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  // Transform data for recharts
  const chartData: ChartDataPoint[] = Object.entries(data).map(([direction, volume]) => ({
    direction,
    volume,
    label: DIRECTION_LABELS[direction as keyof typeof DIRECTION_LABELS]
  }));

  // Generate chart image for PDF
  const generateChartImage = async (): Promise<string> => {
    if (!chartRef.current) return '';
    
    try {
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        logging: false,
        useCORS: true,
        allowTaint: true
      });
      return canvas.toDataURL('image/png', 0.95);
    } catch (error) {
      console.error('Error generating chart image:', error);
      return '';
    }
  };

  useEffect(() => {
    if (onChartReady) {
      const timer = setTimeout(async () => {
        const imageData = await generateChartImage();
        onChartReady(imageData);
      }, 1000); // Delay to ensure chart is fully rendered
      
      return () => clearTimeout(timer);
    }
  }, [onChartReady]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{data.payload.label}</p>
          <p className="text-blue-600">
            Volumen: <span className="font-bold">{data.value.toLocaleString()}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomBar = (props: any) => {
    const { payload } = props;
    const color = CHART_COLORS[payload.direction as keyof typeof CHART_COLORS];
    return <Bar {...props} fill={color} />;
  };

  // If PDF is being generated, show a static placeholder to avoid animation issues
  if (isPDFGenerating) {
    return (
      <div className={`w-full ${className}`}>
        {title && (
          <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
            {title}
          </h3>
        )}
        
        <div 
          ref={chartRef}
          className="w-full bg-white p-4 rounded-lg flex items-center justify-center"
          style={{ minHeight: '400px' }}
        >
          <div className="text-center">
            <div className="text-gray-600 mb-4">Generando gráfico para PDF...</div>
            <div className="text-sm text-gray-500">
              Direcciones: {chartData.length} categorías
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
          {title}
        </h3>
      )}
      
      <div 
        ref={chartRef}
        className="w-full bg-white p-4 rounded-lg"
        style={{ minHeight: '400px' }}
      >
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="label"
              tick={{ fontSize: 12, fill: '#374151' }}
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: '#374151' }}
              stroke="#6b7280"
              label={{ 
                value: 'Volumen de Vehículos', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#374151' }
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="volume" 
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`}
                  fill={CHART_COLORS[entry.direction as keyof typeof CHART_COLORS]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};