"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

/**
 * Reconnect / Disconnect / Refresh controls for the LinkedIn card.
 *
 * The "Connect" and "Reconnect" flows just navigate the browser to the
 * OAuth redirect — the backend sets the state cookie there. Disconnect
 * and Refresh are JSON calls that then reload the page so the server
 * component picks up the new state.
 */
export function LinkedinConnectionActions({
  clientId,
  clientSlug,
  status,
}: {
  clientId: string;
  clientSlug: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<null | "refresh" | "disconnect">(null);

  const connectHref = `/api/linkedin/connect?client_id=${clientId}&next=${encodeURIComponent(
    `/clients/${clientId}`,
  )}`;

  const isConnected = status === "connected";
  const needsAttention =
    status === "needs_reauth" || status === "expired" || status === "revoked";

  const onRefresh = async () => {
    setBusy("refresh");
    try {
      await api.linkedinRefresh(clientSlug);
      router.refresh();
    } finally {
      setBusy(null);
    }
  };

  const onDisconnect = async () => {
    if (
      !confirm(
        "Disconnect LinkedIn for this client? Reports and the MCP server " +
          "will stop working until someone reconnects.",
      )
    ) {
      return;
    }
    setBusy("disconnect");
    try {
      await api.linkedinDisconnect(clientSlug);
      router.refresh();
    } finally {
      setBusy(null);
    }
  };

  if (status === "never") {
    return (
      <a href={connectHref}>
        <Button size="sm">Connect LinkedIn</Button>
      </a>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {needsAttention && (
        <a href={connectHref}>
          <Button size="sm">Reconnect</Button>
        </a>
      )}
      {isConnected && (
        <Button
          size="sm"
          variant="outline"
          onClick={onRefresh}
          disabled={busy !== null}
        >
          {busy === "refresh" ? "Refreshing…" : "Refresh token"}
        </Button>
      )}
      <Button
        size="sm"
        variant="outline"
        onClick={onDisconnect}
        disabled={busy !== null}
      >
        {busy === "disconnect" ? "Disconnecting…" : "Disconnect"}
      </Button>
    </div>
  );
}
