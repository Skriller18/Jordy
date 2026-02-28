export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { jordyFetch } from "@/lib/jordy";

export async function POST(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await req.json().catch(() => ({}));

  const underlyings = Array.isArray(body?.underlyings) ? body.underlyings : ["NIFTY"];
  const horizon = body?.horizon || "short_term";
  const expiry_date = body?.expiry_date || null;
  const include_explanations = body?.include_explanations ?? true;

  const data = await jordyFetch(`/v1/fo/strategies/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ underlyings, horizon, expiry_date, include_explanations }),
  });

  const run = await prisma.run.create({
    data: {
      source: "strategy_lab",
      horizon,
      rawJson: data,
      // ideas are left empty for strategy runs
    },
  });

  return NextResponse.json({ runId: run.id, ...data });
}
