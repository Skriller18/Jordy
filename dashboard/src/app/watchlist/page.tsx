"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type Item = { ticker: string; country: "USA" | "INDIA"; tags: string };

export default function WatchlistPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [ticker, setTicker] = useState("");
  const [country, setCountry] = useState<"USA" | "INDIA">("INDIA");
  const [tags, setTags] = useState("core");

  async function refresh() {
    const res = await fetch("/api/watchlist", { cache: "no-store" });
    const json = await res.json();
    setItems(json.items);
  }

  useEffect(() => {
    refresh();
  }, []);

  const grouped = useMemo(() => {
    return {
      INDIA: items.filter((i) => i.country === "INDIA"),
      USA: items.filter((i) => i.country === "USA"),
    };
  }, [items]);

  async function add() {
    await fetch("/api/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, country, tags }),
    });
    setTicker("");
    await refresh();
  }

  async function remove(i: Item) {
    const url = `/api/watchlist?ticker=${encodeURIComponent(i.ticker)}&country=${encodeURIComponent(i.country)}`;
    await fetch(url, { method: "DELETE" });
    await refresh();
  }

  function renderTable(list: Item[]) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Ticker</TableHead>
            <TableHead>Tags</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {list.map((i) => (
            <TableRow key={`${i.country}-${i.ticker}`}>
              <TableCell className="font-medium">{i.ticker}</TableCell>
              <TableCell>
                {i.tags
                  .split(",")
                  .map((t) => t.trim())
                  .filter(Boolean)
                  .map((t) => (
                    <Badge key={t} variant="secondary" className="mr-1">
                      {t}
                    </Badge>
                  ))}
              </TableCell>
              <TableCell className="text-right">
                <Button variant="destructive" size="sm" onClick={() => remove(i)}>
                  Remove
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Watchlist</h1>
        <p className="text-sm text-muted-foreground">By country. Admins can edit.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add ticker</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <div className="grid gap-1">
            <Label>Ticker</Label>
            <Input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} placeholder="TCS" />
          </div>
          <div className="grid gap-1">
            <Label>Country</Label>
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm"
              value={country}
              onChange={(e) => setCountry(e.target.value as any)}
            >
              <option value="INDIA">INDIA</option>
              <option value="USA">USA</option>
            </select>
          </div>
          <div className="grid gap-1">
            <Label>Tags (comma-separated)</Label>
            <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="core,long" />
          </div>
          <div className="flex items-end">
            <Button onClick={add} disabled={!ticker.trim()}>
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>INDIA</CardTitle>
          </CardHeader>
          <CardContent>{renderTable(grouped.INDIA)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>USA</CardTitle>
          </CardHeader>
          <CardContent>{renderTable(grouped.USA)}</CardContent>
        </Card>
      </div>
    </div>
  );
}
