"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type Snapshot = {
  as_of_epoch_ms: number;
  indices: Record<string, any>;
  warnings: string[];
};

export default function FoIndicesPage() {
  const [data, setData] = useState<Snapshot | null>(null);

  useEffect(() => {
    (async () => {
      const res = await fetch("/api/jordy/v1/fo/indices/snapshot", { cache: "no-store" });
      const json = await res.json();
      setData(json);
    })();
  }, []);

  const rows = data ? Object.entries(data.indices || {}) : [];

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Indices</h1>
        <p className="text-sm text-muted-foreground">NIFTY &amp; SENSEX live snapshot (via Groww).</p>
      </div>

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

      <Card>
        <CardHeader>
          <CardTitle>Snapshot</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Index</TableHead>
                <TableHead>Exchange</TableHead>
                <TableHead>Last</TableHead>
                <TableHead>Day %</TableHead>
                <TableHead>OHLC</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map(([k, v]) => (
                <TableRow key={k}>
                  <TableCell className="font-medium">{k}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{v.exchange}</Badge>
                  </TableCell>
                  <TableCell>{v.last_price ?? "—"}</TableCell>
                  <TableCell>{v.day_change_perc ?? "—"}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {v.ohlc ? `O ${v.ohlc.open} H ${v.ohlc.high} L ${v.ohlc.low} C ${v.ohlc.close}` : "—"}
                  </TableCell>
                </TableRow>
              ))}
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-sm text-muted-foreground">
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
