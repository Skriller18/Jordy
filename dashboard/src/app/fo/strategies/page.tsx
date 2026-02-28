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

type ProxyBacktest = {
  horizon_days: number;
  samples: number;
  avg_return_pct: number;
  median_return_pct: number;
  win_rate_pct: number;
  worst_return_pct: number;
  best_return_pct: number;
};

type Explain = {
  underlying: string;
  strategy: string;
  hypothesis: string[];
  assumptions: string[];
  failure_modes: string[];
  proxy_backtests: ProxyBacktest[];
  notes: string[];
};

type Resp = {
  disclaimer: string;
  best_overall: Pick;
  best_min_risk: Pick;
  best_overall_explain?: Explain | null;
  best_min_risk_explain?: Explain | null;
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
      const res = await fetch("/api/fo/strategies/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ underlyings, horizon: "short_term", include_explanations: true }),
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
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Best overall (profit-seeking)</CardTitle>
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

              {data.best_overall_explain ? (
                <div className="pt-2 space-y-2">
                  <div className="font-medium">Hypothesis</div>
                  <ul className="list-disc pl-5 text-muted-foreground">
                    {data.best_overall_explain.hypothesis.slice(0, 5).map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                  {data.best_overall_explain.proxy_backtests?.length ? (
                    <>
                      <div className="font-medium">Proxy backtest (underlying-only)</div>
                      <ul className="list-disc pl-5 text-muted-foreground">
                        {data.best_overall_explain.proxy_backtests.map((b, i) => (
                          <li key={i}>
                            {b.horizon_days}d: avg {b.avg_return_pct.toFixed(2)}% | win {b.win_rate_pct.toFixed(0)}% | n={b.samples}
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Best minimal-risk (defined-risk preference)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="font-medium">{data.best_min_risk.underlying}</span> → {data.best_min_risk.strategy}{" "}
                <Badge className="ml-2" variant="secondary">
                  {data.best_min_risk.risk}
                </Badge>
              </div>
              <div className="text-muted-foreground">We prefer spreads/iron condor/covered-call style picks; avoid naked high-risk picks.</div>
              <ul className="list-disc pl-5 text-muted-foreground">
                {(data.best_min_risk.rationale || []).slice(0, 5).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>

              {data.best_min_risk_explain ? (
                <div className="pt-2 space-y-2">
                  <div className="font-medium">Hypothesis</div>
                  <ul className="list-disc pl-5 text-muted-foreground">
                    {data.best_min_risk_explain.hypothesis.slice(0, 5).map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                  {data.best_min_risk_explain.proxy_backtests?.length ? (
                    <>
                      <div className="font-medium">Proxy backtest (underlying-only)</div>
                      <ul className="list-disc pl-5 text-muted-foreground">
                        {data.best_min_risk_explain.proxy_backtests.map((b, i) => (
                          <li key={i}>
                            {b.horizon_days}d: avg {b.avg_return_pct.toFixed(2)}% | win {b.win_rate_pct.toFixed(0)}% | n={b.samples}
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
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
                <TableHead className="text-right">Current IV</TableHead>
                <TableHead className="text-right">IV pct</TableHead>
                <TableHead className="text-right">Strike Rates considered</TableHead>
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
                  <TableCell className="text-right">
                    {Number.isFinite((r as any)?.key_metrics?.atm_iv) ? Number((r as any).key_metrics.atm_iv).toFixed(2) : "–"}
                  </TableCell>
                  <TableCell className="text-right">
                    {Number.isFinite((r as any)?.key_metrics?.iv_percentile)
                      ? Number((r as any).key_metrics.iv_percentile).toFixed(0)
                      : "–"}
                  </TableCell>
                  <TableCell className="text-right">
                    {Array.isArray((r as any)?.key_metrics?.strike_prices_considered)
                      ? ((r as any).key_metrics.strike_prices_considered as number[])
                          .slice(0, 6)
                          .map((x) => Number(x).toFixed(0))
                          .join(",")
                      : "–"}
                  </TableCell>
                  <TableCell className="text-right">{r.score.toFixed(0)}</TableCell>
                </TableRow>
              ))}
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-sm text-muted-foreground">
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
