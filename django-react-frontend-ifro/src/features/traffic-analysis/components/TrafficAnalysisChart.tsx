import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { TrafficData } from '../../../shared/types/global.types';

interface TrafficAnalysisChartProps {
  data: TrafficData[];
  title?: string;
  className?: string;
}

export const TrafficAnalysisChart: React.FC<TrafficAnalysisChartProps> = ({ 
  data, 
  title,
  className = '' 
}) => {
  return (
    <div className={`w-full h-96 bg-white p-4 rounded-lg shadow ${className}`}>
      {title && <h3 className="text-lg font-semibold text-center mb-4 text-gray-800">{title}</h3>}
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="hour" 
            tick={{ fontSize: 12, fill: '#4b5563' }} 
            stroke="#6b7280" 
            angle={-45}
            textAnchor="end"
            height={60}
          />
          
          <YAxis 
            yAxisId="volume" 
            orientation="left" 
            label={{ value: '교통량 (대/시간)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#374151' } }}
            tick={{ fontSize: 12, fill: '#4b5563' }}
            stroke="#6b7280"
          />
          
          <YAxis 
            yAxisId="speed" 
            orientation="right" 
            label={{ value: '평균 속도 (km/h)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#374151' } }}
            tick={{ fontSize: 12, fill: '#4b5563' }}
            stroke="#6b7280"
          />
          
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              border: '1px solid #d1d5db',
              borderRadius: '0.5rem',
            }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          
          <Bar yAxisId="volume" dataKey="volume" name="교통량" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          
          <Line yAxisId="speed" type="monotone" dataKey="speed" name="평균 속도" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};