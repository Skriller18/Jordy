-- CreateTable
CREATE TABLE "IvDaily" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "symbol" TEXT NOT NULL,
    "date" DATETIME NOT NULL,
    "iv" REAL NOT NULL,
    "expiryDate" DATETIME,
    "source" TEXT NOT NULL DEFAULT 'unknown',
    "rawJson" JSONB
);

-- CreateIndex
CREATE INDEX "IvDaily_symbol_idx" ON "IvDaily"("symbol");

-- CreateIndex
CREATE INDEX "IvDaily_date_idx" ON "IvDaily"("date");

-- CreateIndex
CREATE UNIQUE INDEX "IvDaily_symbol_date_key" ON "IvDaily"("symbol", "date");
