import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { getAuthUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export const metadata: Metadata = {
  title: "Jordy Dashboard",
  description: "Research dashboard for Jordy",
};

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link className="text-sm text-muted-foreground hover:text-foreground" href={href}>
      {label}
    </Link>
  );
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getAuthUser();

  return (
    <html lang="en">
      <body className="min-h-dvh bg-background text-foreground">
        <header className="border-b">
          <div className="mx-auto flex max-w-6xl items-center justify-between p-4">
            <div className="flex items-center gap-4">
              <Link href="/" className="font-semibold">
                Jordy
              </Link>
              <Separator orientation="vertical" className="h-5" />
              <nav className="flex items-center gap-4">
                <NavLink href="/" label="Dashboard" />
                <NavLink href="/watchlist" label="Watchlist" />
                <NavLink href="/runs" label="Runs" />
                {user?.role === "ADMIN" ? <NavLink href="/admin/invites" label="Admin" /> : null}
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {user ? `${user.role}` : "No session"}
              </span>
              <Button asChild variant="outline" size="sm">
                <a href="/unauthorized">Help</a>
              </Button>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-6xl p-4">{children}</main>
      </body>
    </html>
  );
}
