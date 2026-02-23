import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForbiddenPage() {
  return (
    <div className="mx-auto max-w-lg p-6">
      <Card>
        <CardHeader>
          <CardTitle>Forbidden</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">You don’t have access to that page.</p>
        </CardContent>
      </Card>
    </div>
  );
}
