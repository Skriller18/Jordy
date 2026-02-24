import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function FoHome() {
  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">F&O</h1>
        <p className="text-sm text-muted-foreground">
          Index + NIFTY50 futures/options research (weekly + monthly).
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Indices</CardTitle>
          </CardHeader>
          <CardContent>
            <Link className="underline" href="/fo/indices">
              View NIFTY &amp; SENSEX snapshot
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>NIFTY 50</CardTitle>
          </CardHeader>
          <CardContent>
            <Link className="underline" href="/fo/nifty50">
              View constituents snapshot
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Next</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Next up: option-chain metrics, strategy lab (weekly/monthly), and backtest-permutation runs.
        </CardContent>
      </Card>
    </div>
  );
}
