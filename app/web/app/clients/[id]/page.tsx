import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError, type AuditSummary } from "@/lib/api";
import { serverCookieHeader } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlaybookEditor } from "./playbook-editor";
import { RunAuditButton } from "./run-audit-button";

export const dynamic = "force-dynamic";

export default async function ClientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const cookie = await serverCookieHeader();

  let client: Awaited<ReturnType<typeof api.getClient>>;
  try {
    client = await api.getClient(id, { cookie });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  let initialContent = "";
  let playbookVersion: number | null = null;
  try {
    const pb = await api.getPlaybook(id, { cookie });
    initialContent = pb.content_md;
    playbookVersion = pb.version;
  } catch (e) {
    if (!(e instanceof ApiError && e.status === 404)) throw e;
  }

  let audits: AuditSummary[] = [];
  try {
    const list = await api.listClientAudits(id, { cookie });
    audits = list.items;
  } catch (e) {
    if (!(e instanceof ApiError && e.status === 404)) throw e;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/clients"
            className="text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Clients
          </Link>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{client.name}</h1>
        </div>
        <div className="text-right text-sm text-muted-foreground">
          <div className="font-mono text-xs">slug · {client.slug}</div>
          <div className="font-mono text-xs">
            cid · {client.google_ads_customer_id ?? "—"}
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm md:grid-cols-3">
          <Field label="Timezone" value={client.timezone} />
          <Field label="Currency" value={client.currency} />
          <Field
            label="MCC login"
            value={client.login_customer_id ?? "—"}
            mono
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">
            Playbook{" "}
            {playbookVersion !== null && (
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                v{playbookVersion}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">
            The steering wheel. Every audit, draft action, and report reads
            from this. Use the CLAUDE.md template structure.
          </p>
          <PlaybookEditor clientId={id} initialContent={initialContent} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">Audits</CardTitle>
          <RunAuditButton clientId={id} />
        </CardHeader>
        <CardContent>
          {audits.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No audits yet. Run one to score the account against the
              destructive-defaults framework. Demo data is used until
              Google Ads sync is wired.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/40 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Run</th>
                  <th className="px-3 py-2 font-medium">Score</th>
                  <th className="px-3 py-2 font-medium">Grade</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((a) => (
                  <tr
                    key={a.id}
                    className="border-b border-border last:border-0 hover:bg-muted/30"
                  >
                    <td className="px-3 py-2">
                      <Link
                        href={`/audits/${a.id}`}
                        className="underline-offset-4 hover:underline"
                      >
                        {new Date(a.run_at).toLocaleString()}
                      </Link>
                    </td>
                    <td className="px-3 py-2 font-mono">{a.overall_score}</td>
                    <td className="px-3 py-2">
                      <GradeBadge grade={a.grade} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function GradeBadge({ grade }: { grade: string }) {
  const variant =
    grade === "A"
      ? "success"
      : grade === "B"
        ? "medium"
        : grade === "C"
          ? "high"
          : "critical";
  return <Badge variant={variant}>{grade}</Badge>;
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className={mono ? "font-mono text-xs" : ""}>{value}</div>
    </div>
  );
}
