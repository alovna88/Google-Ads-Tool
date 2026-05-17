"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Action } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ActionQueue({
  initialActions,
  status,
}: {
  initialActions: Action[];
  status: string;
}) {
  const [actions, setActions] = useState(initialActions);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function transition(id: string, t: "approve" | "reject") {
    setBusyId(id);
    setError(null);
    try {
      await api.patchAction(id, t);
      // Drop the row when the filter no longer matches.
      setActions((prev) =>
        status === "proposed" ? prev.filter((a) => a.id !== id) : prev,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "transition failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-3">
      {error && (
        <Card>
          <CardContent className="pt-4 text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      )}
      {actions.map((a) => (
        <ActionRow
          key={a.id}
          action={a}
          busy={busyId === a.id}
          onApprove={() => transition(a.id, "approve")}
          onReject={() => transition(a.id, "reject")}
        />
      ))}
    </div>
  );
}

function ActionRow({
  action,
  busy,
  onApprove,
  onReject,
}: {
  action: Action;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  const isProposed = action.status === "proposed";
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge tier={action.risk_tier} />
              <span className="font-mono text-xs">{action.type}</span>
              <StatusBadge status={action.status} />
            </div>
            <Link
              href={`/clients/${action.client_id}`}
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              {action.client_name}{" "}
              <span className="text-xs font-normal text-muted-foreground">
                · {action.client_slug}
              </span>
            </Link>
          </div>
          {isProposed && (
            <div className="flex shrink-0 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onReject}
                disabled={busy}
              >
                Reject
              </Button>
              <Button size="sm" onClick={onApprove} disabled={busy}>
                {busy ? "Working…" : "Approve"}
              </Button>
            </div>
          )}
        </div>

        <p className="whitespace-pre-wrap text-sm">{action.reasoning_md}</p>

        <div className="grid gap-3 text-xs md:grid-cols-2">
          <DiffBlock title="Diff" data={action.diff} />
          <DiffBlock title="Target" data={action.target} />
        </div>

        {Object.keys(action.expected_impact).length > 0 && (
          <div className="text-xs text-muted-foreground">
            <span className="font-medium uppercase tracking-wide">
              Expected impact:
            </span>{" "}
            {JSON.stringify(action.expected_impact)}
          </div>
        )}

        {action.execution_result && (
          <details>
            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
              Execution result
            </summary>
            <pre className="mt-2 overflow-x-auto rounded-md bg-muted/40 p-3 text-xs">
              {JSON.stringify(action.execution_result, null, 2)}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  );
}

function DiffBlock({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown>;
}) {
  if (Object.keys(data).length === 0) return null;
  return (
    <div className="rounded-md bg-muted/40 p-3">
      <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
        {title}
      </div>
      <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

function RiskBadge({ tier }: { tier: "L1" | "L2" | "L3" }) {
  const variant = tier === "L3" ? "critical" : tier === "L2" ? "high" : "low";
  return <Badge variant={variant}>{tier}</Badge>;
}

function StatusBadge({ status }: { status: Action["status"] }) {
  if (status === "executed") return <Badge variant="success">executed</Badge>;
  if (status === "failed") return <Badge variant="critical">failed</Badge>;
  if (status === "rejected") return <Badge variant="outline">rejected</Badge>;
  if (status === "approved") return <Badge variant="medium">approved</Badge>;
  return <Badge variant="outline">{status}</Badge>;
}
