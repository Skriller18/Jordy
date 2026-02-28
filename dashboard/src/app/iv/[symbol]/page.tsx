"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type Point = {
  date: string;
  iv: number;
  source: string;
  expiryDate?: string | null;
};

export default function IvSymbolPage() {
  const params = useParams();
  const symbol = String((params as any)?.symbol || "").toUpperCase();

  const [days, setDays] = useState(400);
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!symbol) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/iv?symbol=${encodeURIComponent(symbol)}&days=${days}`, { cache: "no-store" });
      const json = await res.json();
      setPoints((json?.points || []).map((p: any) => ({ ...p, date: p.date })));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, days]);

  const chartData = useMemo(() => {
    return (points || []).map((p) => ({
      date: new Date(p.date).toISOString().slice(0, 10),
      iv: p.iv,
      source: p.source,
    }));
  }, [points]);

  const latest = chartData.length ? chartData[chartData.length - 1] : null;

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">IV: {symbol}</h1>
          <p className="text-sm text-muted-foreground">Near-term ATM IV captured daily.</p>
        </div>
        <Link className="text-sm underline" href="/iv">
          Back to IV list
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Range</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-2 flex-wrap">
          <Button variant={days === 30 ? "default" : "outline"} onClick={() => setDays(30)}>
            1M
          </Button>
          <Button variant={days === 90 ? "default" : "outline"} onClick={() => setDays(90)}>
            3M
          </Button>
          <Button variant={days === 180 ? "default" : "outline"} onClick={() => setDays(180)}>
            6M
          </Button>
          <Button variant={days === 365 ? "default" : "outline"} onClick={() => setDays(365)}>
            1Y
          </Button>
          <Button variant={days === 2000 ? "default" : "outline"} onClick={() => setDays(2000)}>
            Max
          </Button>
          <div className="text-sm text-muted-foreground ml-auto">
            {loading ? "Loading…" : latest ? `Latest: ${latest.iv.toFixed(2)} (as of ${latest.date})` : "No data"}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>IV Time Series</CardTitle>
        </CardHeader>
        <CardContent style={{ height: 360 }}>
          {chartData.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
                <YAxis tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
                <Tooltip />
                <Line type="monotone" dataKey="iv" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-sm text-muted-foreground">No IV points to chart yet.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
