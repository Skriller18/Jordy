"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";

type Row = {
  ticker: string;
  exchange: string;
  last_price: number | null;
  day_change_perc: number | null;
};

type Snapshot = {
  as_of_epoch_ms: number;
  rows: Row[];
  warnings: string[];
};

export default function FoNifty50Page() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    (async () => {
      const res = await fetch("/api/jordy/v1/fo/nifty50/snapshot?limit=50", { cache: "no-store" });
      const json = await res.json();
      setData(json);
    })();
  }, []);

  const rows = useMemo(() => {
    const all = data?.rows || [];
    const qq = q.trim().toUpperCase();
    if (!qq) return all;
    return all.filter((r) => r.ticker.includes(qq));
  }, [data, q]);

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">NIFTY 50</h1>
        <p className="text-sm text-muted-foreground">Underlying snapshot (via Groww LTP batch).</p>
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
          <CardTitle>Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search ticker..." />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Snapshot</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticker</TableHead>
                <TableHead>Exchange</TableHead>
                <TableHead className="text-right">LTP</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.ticker}>
                  <TableCell className="font-medium">{r.ticker}</TableCell>
                  <TableCell>{r.exchange}</TableCell>
                  <TableCell className="text-right">{r.last_price ?? "—"}</TableCell>
                </TableRow>
              ))}
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-sm text-muted-foreground">
                    No rows.
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
