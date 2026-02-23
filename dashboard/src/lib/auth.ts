import { cookies } from "next/headers";
import { NextRequest } from "next/server";
import crypto from "crypto";
import { SignJWT, jwtVerify } from "jose";
import { prisma } from "@/lib/db";

const COOKIE_NAME = "jd_session";

function mustEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function sha256Hex(input: string): string {
  return crypto.createHash("sha256").update(input).digest("hex");
}

function secretKey(): Uint8Array {
  const secret = mustEnv("AUTH_SECRET");
  return new TextEncoder().encode(secret);
}

export type AuthUser = {
  id: string;
  role: "ADMIN" | "VIEWER";
  name?: string | null;
};

export function generateOpaqueToken(bytes = 32): string {
  return crypto.randomBytes(bytes).toString("hex");
}

export async function createInviteToken(params: {
  label?: string;
  role: "ADMIN" | "VIEWER";
}): Promise<{ token: string; id: string }> {
  const token = generateOpaqueToken(24);
  const tokenHash = sha256Hex(token);
  const invite = await prisma.inviteToken.create({
    data: {
      label: params.label,
      role: params.role,
      tokenHash,
    },
  });
  return { token, id: invite.id };
}

export async function redeemInviteToken(token: string): Promise<AuthUser> {
  const tokenHash = sha256Hex(token);
  const invite = await prisma.inviteToken.findUnique({ where: { tokenHash } });
  if (!invite) throw new Error("Invalid invite token");
  if (invite.revokedAt) throw new Error("Invite revoked");
  if (invite.usedAt) throw new Error("Invite already used");

  const user = await prisma.user.create({
    data: {
      role: invite.role,
    },
  });

  await prisma.inviteToken.update({
    where: { id: invite.id },
    data: {
      usedAt: new Date(),
      usedById: user.id,
    },
  });

  return { id: user.id, role: user.role, name: user.name };
}

async function signSessionJWT(payload: { sid: string }): Promise<string> {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("30d")
    .sign(secretKey());
}

async function verifySessionJWT(token: string): Promise<{ sid: string } | null> {
  try {
    const { payload } = await jwtVerify(token, secretKey());
    const sid = payload.sid;
    if (typeof sid !== "string") return null;
    return { sid };
  } catch {
    return null;
  }
}

export async function createSession(userId: string): Promise<string> {
  const sessionToken = generateOpaqueToken(32);
  const tokenHash = sha256Hex(sessionToken);
  const expiresAt = new Date(Date.now() + 1000 * 60 * 60 * 24 * 30);

  const sess = await prisma.session.create({
    data: {
      userId,
      tokenHash,
      expiresAt,
    },
  });

  return await signSessionJWT({ sid: sess.id + "." + sessionToken });
}

async function loadSessionFromSid(sidToken: string): Promise<AuthUser | null> {
  const [sid, rawToken] = sidToken.split(".");
  if (!sid || !rawToken) return null;
  const tokenHash = sha256Hex(rawToken);
  const sess = await prisma.session.findUnique({
    where: { id: sid },
    include: { user: true },
  });
  if (!sess) return null;
  if (sess.expiresAt.getTime() < Date.now()) return null;
  if (sess.tokenHash !== tokenHash) return null;
  return { id: sess.user.id, role: sess.user.role, name: sess.user.name };
}

export async function getAuthUser(): Promise<AuthUser | null> {
  const c = await cookies();
  const jwt = c.get(COOKIE_NAME)?.value;
  if (!jwt) return null;
  const verified = await verifySessionJWT(jwt);
  if (!verified) return null;
  return await loadSessionFromSid(verified.sid);
}

export async function getAuthUserFromRequest(req: NextRequest): Promise<AuthUser | null> {
  const jwt = req.cookies.get(COOKIE_NAME)?.value;
  if (!jwt) return null;
  const verified = await verifySessionJWT(jwt);
  if (!verified) return null;
  return await loadSessionFromSid(verified.sid);
}

export async function setSessionCookie(jwt: string): Promise<void> {
  const c = await cookies();
  c.set({
    name: COOKIE_NAME,
    value: jwt,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
}

export function requireRole(user: AuthUser, role: "ADMIN" | "VIEWER"): void {
  if (role === "VIEWER") return;
  if (user.role !== "ADMIN") throw new Error("Forbidden");
}
