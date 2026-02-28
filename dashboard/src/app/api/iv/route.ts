export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const url = new URL(req.url);
  const symbol = (url.searchParams.get("symbol") || "").toUpperCase().trim();
  const days = Math.max(1, Math.min(5000, Number(url.searchParams.get("days") || 400)));

  if (!symbol) return NextResponse.json({ error: "missing_symbol" }, { status: 400 });

  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

  const rows = await prisma.ivDaily.findMany({
    where: { symbol, date: { gte: since } },
    orderBy: { date: "asc" },
    select: { date: true, iv: true, source: true, expiryDate: true },
  });

  return NextResponse.json({ symbol, points: rows });
}
