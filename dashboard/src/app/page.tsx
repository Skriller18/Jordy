export const dynamic = "force-dynamic";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { prisma } from "@/lib/db";
import { Button } from "@/components/ui/button";

async function getSummary() {
  const lastRun = await prisma.run.findFirst({ orderBy: { createdAt: "desc" } });
  let counts = { strong_candidate: 0, watchlist: 0, avoid: 0 };
  if (lastRun) {
    const grouped = await prisma.rankedIdea.groupBy({
      by: ["recommendation"],
      where: { runId: lastRun.id },
      _count: { recommendation: true },
    });
    for (const g of grouped) {
      const key = g.recommendation as keyof typeof counts;
      counts[key] = g._count.recommendation;
    }
  }
  return { lastRun, counts };
}

export default async function DashboardPage() {
  const { lastRun, counts } = await getSummary();

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            {lastRun ? `Last run: ${lastRun.createdAt.toLocaleString()}` : "No runs yet."}
          </p>
        </div>
        <form action="/api/runs" method="post">
          <Button type="submit">Run now</Button>
        </form>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Strong</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{counts.strong_candidate}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Watchlist</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{counts.watchlist}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Avoid</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{counts.avoid}</CardContent>
        </Card>
      </div>

      {lastRun ? (
        <Card>
          <CardHeader>
            <CardTitle>Go to last run</CardTitle>
          </CardHeader>
          <CardContent>
            <a className="underline" href={`/runs/${lastRun.id}`}>
              View results
            </a>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
