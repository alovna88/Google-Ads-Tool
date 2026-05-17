import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError, type AuditCheckResult } from "@/lib/api";
import { serverCookieHeader } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const dynamic = "force-dynamic";

const SEVERITY_RANK = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
} as const;

export default async function AuditDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const cookie = await serverCookieHeader();
  let audit;
  try {
    audit = await api.getAudit(id, { cookie });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  const failed = audit.check_results.filter((c) => !c.passed);
  const passed = audit.check_results.filter((c) => c.passed);
  const sortedFailed = [...failed].sort(
    (a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity],
  );

  return (
    <div className="space-y-6">
      <div>
        <Link
          href={`/clients/${audit.client_id}`}
          className="text-sm text-muted-foreground underline-offset-4 hover:underline"
        >
          ← Client
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Audit</h1>
        <p className="text-sm text-muted-foreground">
          Run {new Date(audit.run_at).toLocaleString()}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <div className="text-sm text-muted-foreground">Overall score</div>
              <div className="font-mono text-3xl">{audit.overall_score}</div>
            </div>
            <GradeBadge grade={audit.grade} large />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Categories</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.entries(audit.category_scores).map(([name, info]) => (
              <div key={name} className="flex items-center justify-between">
                <span className="text-muted-foreground">{name}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono">{info.score}</span>
                  <GradeBadge grade={info.grade} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Failed checks{" "}
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              {failed.length} / {audit.check_results.length}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {sortedFailed.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nothing failed — clean run.
            </p>
          ) : (
            sortedFailed.map((c) => <CheckRow key={c.id} check={c} />)
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Passed{" "}
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              {passed.length}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {passed.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing passed.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {passed.map((c) => (
                <li key={c.id} className="flex items-center gap-2">
                  <Badge variant="success">✓</Badge>
                  <span className="text-muted-foreground">{c.title}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CheckRow({ check }: { check: AuditCheckResult }) {
  return (
    <div className="rounded-md border border-border p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant={check.severity}>{check.severity}</Badge>
            <span className="text-xs font-mono text-muted-foreground">
              {check.check_id}
            </span>
          </div>
          <div className="font-medium">{check.title}</div>
        </div>
        {check.draft_action_id && (
          <Link
            href={`/queue?status=proposed`}
            className="shrink-0 text-xs font-medium underline-offset-4 hover:underline"
          >
            View draft action →
          </Link>
        )}
      </div>
      {check.suggested_fix_md && (
        <p className="mt-3 whitespace-pre-wrap text-sm">{check.suggested_fix_md}</p>
      )}
      {Object.keys(check.evidence).length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
            Evidence
          </summary>
          <pre className="mt-2 overflow-x-auto rounded-md bg-muted/40 p-3 text-xs">
            {JSON.stringify(check.evidence, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function GradeBadge({ grade, large }: { grade: string; large?: boolean }) {
  const variant =
    grade === "A"
      ? "success"
      : grade === "B"
        ? "medium"
        : grade === "C"
          ? "high"
          : "critical";
  return (
    <Badge variant={variant} className={large ? "px-3 py-1 text-lg" : ""}>
      {grade}
    </Badge>
  );
}
