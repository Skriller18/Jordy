export const dynamic = "force-dynamic";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { prisma } from "@/lib/db";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default async function IvHomePage() {
  const syms = await prisma.ivDaily.groupBy({
    by: ["symbol"],
    _count: { _all: true },
    _max: { date: true },
    orderBy: { symbol: "asc" },
  });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">IV</h1>
        <p className="text-sm text-muted-foreground">Implied volatility time series captured daily (near-term ATM).</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Symbols</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead className="text-right">Points</TableHead>
                <TableHead>Last date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {syms.map((s) => (
                <TableRow key={s.symbol}>
                  <TableCell className="font-medium">
                    <Link className="underline" href={`/iv/${s.symbol}`}>
                      {s.symbol}
                    </Link>
                  </TableCell>
                  <TableCell className="text-right">{s._count._all}</TableCell>
                  <TableCell>{s._max.date ? new Date(s._max.date).toLocaleDateString() : "–"}</TableCell>
                </TableRow>
              ))}
              {!syms.length ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-sm text-muted-foreground">
                    No IV data yet.
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
