export const runtime = "nodejs";

import { NextResponse } from "next/server";
import { createSession, redeemInviteToken, setSessionCookie } from "@/lib/auth";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;

  try {
    const user = await redeemInviteToken(token);
    const jwt = await createSession(user.id);
    await setSessionCookie(jwt);
    return NextResponse.redirect(new URL("/", process.env.APP_BASE_URL || "http://localhost:3000"));
  } catch (e: any) {
    return NextResponse.json(
      { error: e?.message || "Invite failed" },
      { status: 400 }
    );
  }
}
