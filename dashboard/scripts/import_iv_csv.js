#!/usr/bin/env node

/**
 * Generic importer for the DailyNC*.csv files that contain an IV column.
 *
 * Usage:
 *   node scripts/import_iv_csv.js <SYMBOL> <CSV_PATH> [LOOKBACK=252]
 *
 * Example:
 *   node scripts/import_iv_csv.js NIFTY /path/to/DailyNCNIFTY.csv 252
 */

import fs from "fs";
import { PrismaClient } from "@prisma/client";

const symbol = String(process.argv[2] || "").toUpperCase().trim();
const CSV_PATH = process.argv[3];
const LOOKBACK = Number(process.argv[4] || 252);

if (!symbol || !CSV_PATH) {
  console.error("Usage: node scripts/import_iv_csv.js <SYMBOL> <CSV_PATH> [LOOKBACK=252]");
  process.exit(2);
}

function parseDate(d) {
  // format: 27-Feb-2026
  const [dd, mon, yyyy] = d.split("-");
  const months = {
    Jan: 0,
    Feb: 1,
    Mar: 2,
    Apr: 3,
    May: 4,
    Jun: 5,
    Jul: 6,
    Aug: 7,
    Sep: 8,
    Oct: 9,
    Nov: 10,
    Dec: 11,
  };
  const m = months[mon];
  if (m === undefined) throw new Error("bad month: " + mon);
  return new Date(Date.UTC(Number(yyyy), m, Number(dd), 0, 0, 0));
}

function splitCSVLine(line) {
  // Simple CSV parser: these files are numeric and don't include quoted commas.
  return line.split(",");
}

const text = fs.readFileSync(CSV_PATH, "utf8");
const lines = text.split(/\r?\n/).filter(Boolean);
if (lines.length < 3) {
  console.error("CSV too small");
  process.exit(1);
}

const header = splitCSVLine(lines[0]);
const idxDate = header.indexOf("Date");
const idxIV = header.findIndex((h) => h.trim().toUpperCase().startsWith("IV"));

if (idxDate === -1 || idxIV === -1) {
  console.error("Could not find Date or IV column");
  process.exit(1);
}

const rows = [];
for (let i = 1; i < lines.length; i++) {
  const cols = splitCSVLine(lines[i]);
  if (cols.length <= Math.max(idxDate, idxIV)) continue;
  const d = cols[idxDate]?.trim();
  const ivStr = cols[idxIV]?.trim();
  if (!d) continue;
  const iv = Number(ivStr);
  if (!Number.isFinite(iv) || iv <= 0) continue;
  rows.push({ date: parseDate(d), iv, raw: lines[i] });
}

// file appears newest-first; normalize then take last LOOKBACK (most recent)
rows.sort((a, b) => a.date.getTime() - b.date.getTime());
const slice = rows.slice(Math.max(0, rows.length - LOOKBACK));

const prisma = new PrismaClient();

let upserts = 0;
for (const r of slice) {
  await prisma.ivDaily.upsert({
    where: { symbol_date: { symbol, date: r.date } },
    update: { iv: r.iv, source: "csv_daily_nca", rawJson: { csv: r.raw, file: CSV_PATH } },
    create: { symbol, date: r.date, iv: r.iv, source: "csv_daily_nca", rawJson: { csv: r.raw, file: CSV_PATH } },
  });
  upserts++;
}

await prisma.$disconnect();
console.log(JSON.stringify({ ok: true, symbol, imported: upserts, from: CSV_PATH }));
