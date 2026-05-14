"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type Status = "idle" | "saving" | "saved" | "error";

export function PlaybookEditor({
  clientId,
  initialContent,
}: {
  clientId: string;
  initialContent: string;
}) {
  const [content, setContent] = useState(initialContent);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [savedVersion, setSavedVersion] = useState<number | null>(null);

  async function onSave() {
    setStatus("saving");
    setError(null);
    try {
      const saved = await api.savePlaybook(clientId, content);
      setSavedVersion(saved.version);
      setStatus("saved");
    } catch (e) {
      setError(e instanceof Error ? e.message : "save failed");
      setStatus("error");
    }
  }

  function loadTemplate() {
    if (
      content.trim() &&
      !confirm("Replace current content with the empty template?")
    ) {
      return;
    }
    setContent(TEMPLATE_STARTER);
  }

  return (
    <div className="space-y-3">
      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="min-h-[28rem]"
        placeholder="Paste the CLAUDE.md template and fill in the brackets…"
      />
      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          {status === "saving" && "Saving…"}
          {status === "saved" && savedVersion !== null && (
            <>Saved as v{savedVersion}.</>
          )}
          {status === "error" && (
            <span className="text-destructive">Error: {error}</span>
          )}
          {status === "idle" && content === initialContent && "No changes."}
          {status === "idle" && content !== initialContent && "Unsaved changes."}
        </div>
        <div className="flex gap-2">
          {!content.trim() && (
            <Button variant="outline" onClick={loadTemplate}>
              Load template
            </Button>
          )}
          <Button
            onClick={onSave}
            disabled={status === "saving" || content === initialContent}
          >
            Save new version
          </Button>
        </div>
      </div>
    </div>
  );
}

// Inline starter — short version so the editor isn't empty for first-time
// users. The full template lives at skills/CLAUDE.md.template.
const TEMPLATE_STARTER = `# Agency Google Ads Workspace — [CLIENT NAME]

## 1. Client identity

- **Company**: [CLIENT NAME]
- **Product**: [ONE SENTENCE]
- **ICP**: [TITLE], [COMPANY SIZE], [INDUSTRY]
- **ACV (annual contract value)**: $[NUMBER]
- **Sales cycle**: [NUMBER] days
- **Currency**: [USD]
- **Reporting timezone**: [America/New_York]
- **Google Ads CID**: [123-456-7890]

## 2. Targets

- **Target CAC**: $[NUMBER]
- **Target LTV:CAC**: 3.0
- **Primary success metric**: [Closed-Won pipeline / SQL volume]

(See skills/CLAUDE.md.template for the full structure: conversion hierarchy,
account structure, bidding rules, negatives, brand voice, approval thresholds.)
`;
