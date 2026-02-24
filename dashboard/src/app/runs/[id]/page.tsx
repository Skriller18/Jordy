export const dynamic = "force-dynamic";

import Link from "next/link";
import { prisma } from "@/lib/db";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function recBadge(rec: string) {
  if (rec === "strong_candidate") return <Badge className="bg-emerald-600">strong</Badge>;
  if (rec === "watchlist") return <Badge className="bg-sky-600">watchlist</Badge>;
  return <Badge variant="secondary">avoid</Badge>;
}

export default async function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = await prisma.run.findUnique({
    where: { id },
    include: { ideas: { orderBy: { compositeScore: "desc" } } },
  });

  if (!run) return <div>Run not found.</div>;

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Run</h1>
        <p className="text-sm text-muted-foreground">
          {run.createdAt.toLocaleString()} • {run.source} • {run.horizon}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ranked ideas</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticker</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Rec</TableHead>
                <TableHead className="text-right">Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {run.ideas.map((i) => (
                <TableRow key={i.id}>
                  <TableCell className="font-medium">
                    <Link className="underline" href={`/companies/${i.ticker}`}>
                      {i.ticker}
                    </Link>
                  </TableCell>
                  <TableCell>{i.companyName}</TableCell>
                  <TableCell>{i.country}</TableCell>
                  <TableCell>{recBadge(i.recommendation)}</TableCell>
                  <TableCell className="text-right">{i.compositeScore.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="text-sm text-muted-foreground">
        Tip: click a ticker to view its detail page.
      </div>

      <Link className="underline text-sm" href="/runs">
        Back to runs
      </Link>
    </div>
  );
}
