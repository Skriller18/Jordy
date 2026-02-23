export const runtime = "nodejs";

import { NextRequest, NextResponse } from "next/server";
import { createInviteToken, getAuthUserFromRequest } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { z } from "zod";

const CreateSchema = z.object({
  label: z.string().optional(),
  role: z.enum(["ADMIN", "VIEWER"]).default("VIEWER"),
});

export async function GET(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const invites = await prisma.inviteToken.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
    include: { usedBy: true },
  });
  const users = await prisma.user.findMany({ orderBy: { createdAt: "desc" }, take: 100 });
  return NextResponse.json({ invites, users });
}

export async function POST(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const body = CreateSchema.parse(await req.json());
  const created = await createInviteToken({ label: body.label, role: body.role });
  return NextResponse.json({ token: created.token, id: created.id });
}

export async function DELETE(req: NextRequest) {
  const user = await getAuthUserFromRequest(req);
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (user.role !== "ADMIN") return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "missing" }, { status: 400 });
  await prisma.inviteToken.update({ where: { id }, data: { revokedAt: new Date() } });
  return NextResponse.json({ ok: true });
}
