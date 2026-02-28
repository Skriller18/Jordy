export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const rows = await prisma.ivDaily.groupBy({
    by: ["symbol"],
    _count: { _all: true },
    _max: { date: true },
    orderBy: { symbol: "asc" },
  });

  return NextResponse.json({
    symbols: rows.map((r) => ({ symbol: r.symbol, count: r._count._all, lastDate: r._max.date })),
  });
}
