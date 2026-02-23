"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type Invite = {
  id: string;
  createdAt: string;
  revokedAt?: string | null;
  usedAt?: string | null;
  label?: string | null;
  role: "ADMIN" | "VIEWER";
  usedBy?: { id: string; role: string } | null;
};

type User = { id: string; createdAt: string; role: "ADMIN" | "VIEWER"; name?: string | null };

export default function AdminInvitesPage() {
  const [invites, setInvites] = useState<Invite[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [label, setLabel] = useState("");
  const [role, setRole] = useState<"ADMIN" | "VIEWER">("VIEWER");
  const [newToken, setNewToken] = useState<string | null>(null);

  async function refresh() {
    const res = await fetch("/api/admin/invites", { cache: "no-store" });
    const json = await res.json();
    setInvites(json.invites);
    setUsers(json.users);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function create() {
    const res = await fetch("/api/admin/invites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: label || undefined, role }),
    });
    const json = await res.json();
    setNewToken(json.token);
    setLabel("");
    await refresh();
  }

  async function revoke(id: string) {
    await fetch(`/api/admin/invites?id=${encodeURIComponent(id)}`, { method: "DELETE" });
    await refresh();
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Admin</h1>
        <p className="text-sm text-muted-foreground">Manage trusted-user invite tokens and users.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create invite token</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <div className="grid gap-1">
            <Label>Label</Label>
            <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Subhash friend" />
          </div>
          <div className="grid gap-1">
            <Label>Role</Label>
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value as any)}
            >
              <option value="VIEWER">VIEWER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>
          <div className="flex items-end">
            <Button onClick={create}>Create</Button>
          </div>
          <div className="md:col-span-4">
            {newToken ? (
              <div className="rounded-md border p-3 text-sm">
                <div className="font-medium">Invite token (copy once):</div>
                <div className="mt-1 font-mono break-all">{newToken}</div>
                <div className="mt-2 text-muted-foreground">
                  Invite URL: <span className="font-mono">/invite/{newToken}</span>
                </div>
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invites</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Created</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Label</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invites.map((i) => {
                const status = i.revokedAt
                  ? "revoked"
                  : i.usedAt
                    ? `used (${i.usedBy?.role || ""})`
                    : "active";
                return (
                  <TableRow key={i.id}>
                    <TableCell>{new Date(i.createdAt).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge variant={i.role === "ADMIN" ? "default" : "secondary"}>{i.role}</Badge>
                    </TableCell>
                    <TableCell>{i.label || "—"}</TableCell>
                    <TableCell>{status}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => revoke(i.id)}
                        disabled={!!i.revokedAt}
                      >
                        Revoke
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Created</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>User ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>{new Date(u.createdAt).toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant={u.role === "ADMIN" ? "default" : "secondary"}>{u.role}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{u.id}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
