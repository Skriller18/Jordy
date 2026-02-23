"use client";

import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from "recharts";

export function ScoreBreakdown({
  quant,
  qual,
}: {
  quant: Record<string, number>;
  qual: Record<string, number>;
}) {
  const keys = Array.from(
    new Set([...Object.keys(quant || {}), ...Object.keys(qual || {})])
  );
  const data = keys.map((k) => ({
    k,
    quant: quant?.[k] ?? 0,
    qual: qual?.[k] ?? 0,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="k" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          <Tooltip />
          <Radar
            name="Quant"
            dataKey="quant"
            stroke="#2563eb"
            fill="#2563eb"
            fillOpacity={0.25}
          />
          <Radar
            name="Qual"
            dataKey="qual"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
