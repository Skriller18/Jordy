export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { z } from "zod";

const CreateSchema = z.object({
  ticker: z.string().min(1).max(30),
  country: z.enum(["USA", "INDIA"]),
  tags: z.string().optional().default(""),
});

export async function GET(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const items = await prisma.watchlistItem.findMany({
    orderBy: [{ country: "asc" }, { ticker: "asc" }],
  });
  return NextResponse.json({ items });
}

export async function POST(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const json = await req.json();
  const data = CreateSchema.parse(json);
  const item = await prisma.watchlistItem.upsert({
    where: { ticker_country: { ticker: data.ticker.toUpperCase(), country: data.country } },
    update: { tags: data.tags },
    create: { ticker: data.ticker.toUpperCase(), country: data.country, tags: data.tags },
  });
  return NextResponse.json({ item });
}

export async function DELETE(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const { searchParams } = new URL(req.url);
  const ticker = searchParams.get("ticker")?.toUpperCase();
  const country = searchParams.get("country") as "USA" | "INDIA" | null;
  if (!ticker || !country) return NextResponse.json({ error: "missing" }, { status: 400 });

  await prisma.watchlistItem.delete({ where: { ticker_country: { ticker, country } } });
  return NextResponse.json({ ok: true });
}
