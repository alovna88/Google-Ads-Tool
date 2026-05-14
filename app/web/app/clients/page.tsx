import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  let clients: Awaited<ReturnType<typeof api.listClients>> | null = null;
  let error: string | null = null;

  try {
    clients = await api.listClients();
  } catch (e) {
    error = e instanceof Error ? e.message : "failed to load clients";
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Clients</h1>
        <Link href="/clients/new">
          <Button>New client</Button>
        </Link>
      </div>

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">
              Couldn&apos;t load clients: {error}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Is the API up? Try <code className="font-mono">curl localhost:8000/health</code>.
            </p>
          </CardContent>
        </Card>
      )}

      {!error && clients && clients.items.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              No clients yet. Create one to get started.
            </p>
          </CardContent>
        </Card>
      )}

      {!error && clients && clients.items.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr className="text-left">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Slug</th>
                  <th className="px-4 py-3 font-medium">Google Ads CID</th>
                  <th className="px-4 py-3 font-medium">Currency</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {clients.items.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-border last:border-0 hover:bg-muted/30"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/clients/${c.id}`}
                        className="font-medium underline-offset-4 hover:underline"
                      >
                        {c.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      {c.slug}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {c.google_ads_customer_id ?? <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className="px-4 py-3">{c.currency}</td>
                    <td className="px-4 py-3">
                      {c.active ? (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-800">
                          active
                        </span>
                      ) : (
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                          inactive
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
