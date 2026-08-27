import { api, ApiError, type LinkedinAdAccount, type LinkedinHealth } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LinkedinConnectionActions } from "./linkedin-connection-actions";

/**
 * Server component: pulls the connection health + cached ad accounts on
 * every render (page is `force-dynamic`), then hands the interactive
 * buttons to the client component below the status area.
 *
 * When status = "never" no accounts are fetched — the connection
 * simply doesn't exist yet.
 */
export async function LinkedinCard({
  clientId,
  clientSlug,
  cookie,
}: {
  clientId: string;
  clientSlug: string;
  cookie: string;
}) {
  let health: LinkedinHealth | null = null;
  try {
    health = await api.linkedinHealth(clientSlug, { cookie });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      // Client not found by slug on the linkedin router — bail gracefully
      // rather than 500ing the whole page.
      return null;
    }
    throw e;
  }

  let accounts: LinkedinAdAccount[] = [];
  if (health.status !== "never") {
    try {
      accounts = await api.linkedinAdAccounts(clientSlug, { cookie });
    } catch (e) {
      // 409 = not connected (shouldn't happen given the guard above),
      // anything else we swallow silently — the card still shows status.
      if (!(e instanceof ApiError)) throw e;
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">LinkedIn Ads</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Read-only. Powers the MCP server + <code>/linkedin-ads-report</code>{" "}
            skill.
          </p>
        </div>
        <LinkedinConnectionActions
          clientId={clientId}
          clientSlug={clientSlug}
          status={health.status}
        />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 text-sm md:grid-cols-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Status
            </div>
            <StatusBadge status={health.status} />
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Token expiry
            </div>
            <div className="text-sm">{formatExpiry(health)}</div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Last refreshed
            </div>
            <div className="text-sm">
              {health.last_refreshed_at
                ? new Date(health.last_refreshed_at).toLocaleString()
                : "—"}
            </div>
          </div>
        </div>

        {health.last_error && (
          <div className="rounded-md border border-orange-200 bg-orange-50 px-3 py-2 text-xs text-orange-900">
            <div className="font-medium">Last error</div>
            <div className="mt-1 font-mono">{health.last_error}</div>
          </div>
        )}

        {health.status === "never" ? (
          <p className="text-sm text-muted-foreground">
            No LinkedIn connection. Click{" "}
            <span className="font-medium">Connect LinkedIn</span> to
            authorize this client&rsquo;s account. Once connected, the
            worker keeps the token alive automatically.
          </p>
        ) : accounts.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Connected, but no ad accounts visible yet. Try{" "}
            <span className="font-medium">Refresh token</span> or check
            that the authorized member has been added to the LinkedIn ad
            account.
          </p>
        ) : (
          <div>
            <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
              Ad accounts ({accounts.length})
            </div>
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/40 text-left">
                <tr>
                  <th className="px-3 py-1 font-medium">Name</th>
                  <th className="px-3 py-1 font-medium">ID</th>
                  <th className="px-3 py-1 font-medium">Role</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.urn} className="border-b border-border last:border-0">
                    <td className="px-3 py-1">{a.name ?? "—"}</td>
                    <td className="px-3 py-1 font-mono text-xs">{a.id}</td>
                    <td className="px-3 py-1 text-xs text-muted-foreground">
                      {a.role ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: LinkedinHealth["status"] }) {
  const variant =
    status === "connected"
      ? "success"
      : status === "needs_reauth" || status === "revoked"
        ? "critical"
        : status === "expired" || status === "error"
          ? "high"
          : "outline";
  const label =
    status === "never"
      ? "Not connected"
      : status === "needs_reauth"
        ? "Needs re-auth"
        : status.replace("_", " ");
  return <Badge variant={variant}>{label}</Badge>;
}

function formatExpiry(health: LinkedinHealth): string {
  if (!health.expires_at) return "—";
  const at = new Date(health.expires_at);
  const secs = health.seconds_until_expiry ?? 0;
  if (secs <= 0) return `${at.toLocaleString()} (expired)`;
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const rel = days > 0 ? `in ${days}d ${hours}h` : `in ${hours}h`;
  return `${at.toLocaleString()} (${rel})`;
}
