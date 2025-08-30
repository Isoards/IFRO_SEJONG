import React, { useRef, useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import html2canvas from 'html2canvas';
import { TrafficData } from '../../../shared/types/global.types';

interface TrafficTimeLineChartProps {
  data: TrafficData[];
  title?: string;
  onChartReady?: (chartImage: string) => void;
  className?: string;
  showVolume?: boolean;
  showSpeed?: boolean;
  isPDFGenerating?: boolean;
}

export const TrafficTimeLineChart: React.FC<TrafficTimeLineChartProps> = ({
  data,
  title = 'Variación del Tráfico en el Tiempo',
  onChartReady,
  className = '',
  showVolume = true,
  showSpeed = true,
  isPDFGenerating = false
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

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
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800 mb-2">Hora: {label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: <span className="font-bold">
                {entry.name === 'Volumen' 
                  ? entry.value.toLocaleString() 
                  : `${entry.value} km/h`
                }
              </span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Format hour for display
  const formatHour = (hour: string) => {
    // If hour is already formatted (e.g., "14:00"), return as is
    if (hour.includes(':')) return hour;
    
    // If hour is a number, format it
    const hourNum = parseInt(hour);
    return `${hourNum.toString().padStart(2, '0')}:00`;
  };

  // Process data to ensure proper formatting
  const processedData = data.map(item => ({
    ...item,
    hour: formatHour(item.hour)
  }));

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
              Datos: {processedData.length} puntos de tiempo
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
          <LineChart
            data={processedData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 20
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="hour"
              tick={{ fontSize: 12, fill: '#374151' }}
              stroke="#6b7280"
            />
            <YAxis 
              yAxisId="volume"
              orientation="left"
              tick={{ fontSize: 12, fill: '#374151' }}
              stroke="#6b7280"
              label={{ 
                value: 'Volumen de Vehículos', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#374151' }
              }}
            />
            {showSpeed && (
              <YAxis 
                yAxisId="speed"
                orientation="right"
                tick={{ fontSize: 12, fill: '#374151' }}
                stroke="#6b7280"
                label={{ 
                  value: 'Velocidad (km/h)', 
                  angle: 90, 
                  position: 'insideRight',
                  style: { textAnchor: 'middle', fill: '#374151' }
                }}
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            
            {showVolume && (
              <Line
                yAxisId="volume"
                type="monotone"
                dataKey="volume"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                name="Volumen"
                isAnimationActive={false}
              />
            )}
            
            {showSpeed && (
              <Line
                yAxisId="speed"
                type="monotone"
                dataKey="speed"
                stroke="#ef4444"
                strokeWidth={3}
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#ef4444', strokeWidth: 2 }}
                name="Velocidad"
                isAnimationActive={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};