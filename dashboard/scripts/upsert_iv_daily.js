#!/usr/bin/env node

// Usage:
//   node scripts/upsert_iv_daily.js --json '{"symbol":"ADANIENT","date":"2026-02-28","iv":30.5,"expiry_date":"2026-03-05","source":"groww_chain"}'

import { PrismaClient } from "@prisma/client";

function parseArgs() {
  const out = { json: null };
  for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--json") out.json = process.argv[++i];
  }
  return out;
}

const { json } = parseArgs();
if (!json) {
  console.error("Missing --json");
  process.exit(2);
}

let payload;
try {
  payload = JSON.parse(json);
} catch (e) {
  console.error("Bad JSON payload");
  process.exit(2);
}

const symbol = String(payload.symbol || "").toUpperCase().trim();
const dateStr = String(payload.date || "").trim();
const iv = payload.iv;
const expiryDateStr = payload.expiry_date ? String(payload.expiry_date) : null;
const source = String(payload.source || "unknown");

if (!symbol || !dateStr || !Number.isFinite(iv)) {
  console.error("Payload must include symbol, date (YYYY-MM-DD), iv (number)");
  process.exit(2);
}

const prisma = new PrismaClient();

const date = new Date(dateStr + "T00:00:00.000Z");
const expiryDate = expiryDateStr ? new Date(expiryDateStr + "T00:00:00.000Z") : null;

const rawJson = payload;

await prisma.ivDaily.upsert({
  where: { symbol_date: { symbol, date } },
  update: { iv: Number(iv), expiryDate, source, rawJson },
  create: { symbol, date, iv: Number(iv), expiryDate, source, rawJson },
});

await prisma.$disconnect();
console.log("ok");
