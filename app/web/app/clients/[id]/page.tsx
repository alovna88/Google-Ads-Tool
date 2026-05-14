import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { serverCookieHeader } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlaybookEditor } from "./playbook-editor";

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
    </div>
  );
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
