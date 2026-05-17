"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function RunAuditButton({ clientId }: { clientId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    try {
      // No snapshot in the body — backend falls back to the demo fixture
      // so we can run an audit before Google Ads sync exists. Pass a
      // real snapshot once we have one.
      const audit = await api.runAudit(clientId, null);
      router.push(`/audits/${audit.id}`);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "audit run failed");
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <Button onClick={onClick} disabled={busy}>
        {busy ? "Running audit…" : "Run audit"}
      </Button>
      {error && <span className="text-sm text-destructive">{error}</span>}
    </div>
  );
}
