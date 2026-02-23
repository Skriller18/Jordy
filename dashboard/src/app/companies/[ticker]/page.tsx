import { prisma } from "@/lib/db";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreBreakdown } from "@/components/charts/ScoreBreakdown";

function recBadge(rec: string) {
  if (rec === "strong_candidate") return <Badge className="bg-emerald-600">strong</Badge>;
  if (rec === "watchlist") return <Badge className="bg-sky-600">watchlist</Badge>;
  return <Badge variant="secondary">avoid</Badge>;
}

function listBlock(title: string, items: any) {
  const arr = Array.isArray(items) ? items : [];
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {arr.length ? arr.map((x, idx) => <li key={idx}>{String(x)}</li>) : <li>—</li>}
        </ul>
      </CardContent>
    </Card>
  );
}

export default async function CompanyPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  const idea = await prisma.rankedIdea.findFirst({
    where: { ticker: ticker.toUpperCase() },
    orderBy: { createdAt: "desc" },
    include: { run: true },
  });

  if (!idea) return <div>Not found.</div>;

  const score = idea.scoreJson as any;

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {idea.ticker} <span className="text-muted-foreground">— {idea.companyName}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            {idea.country} • {recBadge(idea.recommendation)} • composite {idea.compositeScore.toFixed(2)}
          </p>
          <p className="text-xs text-muted-foreground">From run: {idea.run.createdAt.toLocaleString()}</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Score breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <ScoreBreakdown quant={score?.quant_components || {}} qual={score?.qual_components || {}} />
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        {listBlock("Positives", idea.positivesJson)}
        {listBlock("Negatives", idea.negativesJson)}
        {listBlock("Risk notes", idea.riskNotesJson)}
      </div>
    </div>
  );
}
