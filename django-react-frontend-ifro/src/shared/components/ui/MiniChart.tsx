import React, { memo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TrafficData } from "../../types/global.types";

interface MiniChartProps {
  data: TrafficData[];
  dataKey: keyof TrafficData;
  color: string;
  showAxis?: boolean;
}

export const MiniChart = memo<MiniChartProps>(
  ({ data, dataKey, color, showAxis = false }) => (
    <ResponsiveContainer width="100%" height={showAxis ? 180 : "100%"}>
      <AreaChart data={data} margin={{ top: 5, right: 0, left: 0, bottom: 5 }}>
        {showAxis && (
          <>
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 12, fill: "#888" }}
              stroke="#888"
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#888" }}
              stroke="#888"
              domain={[0, "dataMax + 100"]}
              tickCount={6}
              axisLine={true}
              tickLine={true}
            />
          </>
        )}
        <Tooltip
          contentStyle={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "0.5rem",
            fontSize: "0.75rem",
            color: "#1f2937",
          }}
          labelStyle={{ fontWeight: "bold" }}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          fill={color}
          fillOpacity={0.1}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
);

MiniChart.displayName = "MiniChart";
