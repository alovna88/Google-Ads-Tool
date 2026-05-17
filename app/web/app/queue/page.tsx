import Link from "next/link";
import { api } from "@/lib/api";
import { serverCookieHeader } from "@/lib/auth";
import { Card, CardContent } from "@/components/ui/card";
import { ActionQueue } from "./action-queue";

export const dynamic = "force-dynamic";

export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const sp = await searchParams;
  const status = sp.status ?? "proposed";

  const cookie = await serverCookieHeader();
  const list = await api.listActions({ cookie, status });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Action Queue</h1>
          <p className="text-sm text-muted-foreground">
            Drafts proposed by audits across all clients. Approve to execute
            (stub for now — real Google Ads writes land with slice B).
          </p>
        </div>
        <Filters current={status} />
      </div>

      {list.items.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              No actions in <span className="font-mono">{status}</span>.
              {status !== "proposed" && (
                <>
                  {" "}
                  <Link
                    href="/queue"
                    className="underline-offset-4 hover:underline"
                  >
                    Show proposed
                  </Link>
                  .
                </>
              )}
            </p>
          </CardContent>
        </Card>
      ) : (
        <ActionQueue initialActions={list.items} status={status} />
      )}
    </div>
  );
}

const STATUSES = ["proposed", "approved", "executed", "rejected", "failed"];

function Filters({ current }: { current: string }) {
  return (
    <div className="flex items-center gap-1 text-sm">
      {STATUSES.map((s) => (
        <Link
          key={s}
          href={`/queue?status=${s}`}
          className={
            s === current
              ? "rounded-md bg-primary px-2 py-1 text-primary-foreground"
              : "rounded-md px-2 py-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          }
        >
          {s}
        </Link>
      ))}
    </div>
  );
}
