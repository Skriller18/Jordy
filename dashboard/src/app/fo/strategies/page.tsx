"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type Pick = {
  underlying: string;
  strategy: string;
  risk: "low" | "medium" | "high";
  expected_edge: string;
  score: number;
  rationale: string[];
  key_metrics: any;
};

type Resp = {
  disclaimer: string;
  best_overall: Pick;
  results: Pick[];
  warnings: string[];
};

export default function FoStrategiesPage() {
  const [data, setData] = useState<Resp | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      // Run for NIFTY + all NIFTY50 underlyings (50)
      const uni = await fetch("/api/jordy/v1/fo/universe", { cache: "no-store" }).then((r) => r.json());
      const underlyings = ["NIFTY", ...(uni?.nifty50 || [])];
      const res = await fetch("/api/jordy/v1/fo/strategies/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ underlyings, horizon: "short_term" }),
      });
      const json = await res.json();
      setData(json);
    } finally {
      setLoading(false);
    }
  }

  const rows = useMemo(() => data?.results || [], [data]);

  useEffect(() => {
    // auto-run once on first load
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Strategy Lab</h1>
        <p className="text-sm text-muted-foreground">
          Research-only heuristic strategy picks using option-chain data (Groww → NSE fallback). Not advice.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Controls</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Button onClick={run} disabled={loading}>
            {loading ? "Running…" : "Run for NIFTY + NIFTY50"}
          </Button>
          <Link className="text-sm underline" href="/fo">
            Back to F&O
          </Link>
        </CardContent>
      </Card>

      {data?.warnings?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Warnings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {data.warnings.map((w, i) => (
              <div key={i} className="text-muted-foreground">
                {w}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {data && rows.every((r) => r.strategy === "no_data") ? (
        <Card>
          <CardHeader>
            <CardTitle>Option chain data unavailable</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Option chain returned 0 strikes (or empty payload), so strategy picks are blocked. Try again during market hours.
          </CardContent>
        </Card>
      ) : null}

      {data ? (
        <Card>
          <CardHeader>
            <CardTitle>Best overall (by heuristic score)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              <span className="font-medium">{data.best_overall.underlying}</span> → {data.best_overall.strategy}{" "}
              <Badge className="ml-2" variant="secondary">
                {data.best_overall.risk}
              </Badge>
            </div>
            <div className="text-muted-foreground">{data.disclaimer}</div>
            <ul className="list-disc pl-5 text-muted-foreground">
              {(data.best_overall.rationale || []).slice(0, 5).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Underlying</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead className="text-right">Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.underlying}>
                  <TableCell className="font-medium">{r.underlying}</TableCell>
                  <TableCell>{r.strategy}</TableCell>
                  <TableCell>
                    <Badge variant={r.risk === "low" ? "secondary" : r.risk === "medium" ? "outline" : "destructive"}>
                      {r.risk}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{r.score.toFixed(0)}</TableCell>
                </TableRow>
              ))}
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-sm text-muted-foreground">
                    No data yet.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
