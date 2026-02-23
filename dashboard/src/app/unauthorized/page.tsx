import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function UnauthorizedPage() {
  return (
    <div className="mx-auto max-w-lg p-6">
      <Card>
        <CardHeader>
          <CardTitle>Not signed in</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            You need an invite link from an admin to access this dashboard.
          </p>
          <p className="text-sm">
            If you have an invite token, open the invite URL (e.g. /invite/&lt;token&gt;).
          </p>
          <Link className="text-sm underline" href="/">
            Go home
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
