export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { jordyFetch } from "@/lib/jordy";

export async function GET(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const runs = await prisma.run.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
    include: { ideas: true },
  });
  return NextResponse.json({ runs });
}

export async function POST(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const body = await req.json().catch(() => ({}));
  const horizon = body?.horizon || "long_term";

  const data = await jordyFetch(`/v1/sample?horizon=${encodeURIComponent(horizon)}`);

  const run = await prisma.run.create({
    data: {
      source: "sample",
      horizon,
      rawJson: data,
      ideas: {
        create: (data.results || []).map((r: any) => ({
          ticker: r.ticker,
          companyName: r.company_name,
          country: r.country,
          recommendation: r.recommendation,
          compositeScore: r.score?.composite_score ?? 0,
          scoreJson: r.score,
          positivesJson: r.positives ?? [],
          negativesJson: r.negatives ?? [],
          riskNotesJson: r.risk_notes ?? [],
        })),
      },
    },
    include: { ideas: true },
  });

  return NextResponse.json({ run });
}
