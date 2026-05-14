"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function NewClientPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    google_ads_customer_id: "",
    login_customer_id: "",
    timezone: "America/New_York",
    currency: "USD",
  });

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: form.name,
        slug: form.slug,
        google_ads_customer_id: form.google_ads_customer_id || null,
        login_customer_id: form.login_customer_id || null,
        timezone: form.timezone,
        currency: form.currency,
      };
      const created = await api.createClient(payload);
      router.push(`/clients/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "create failed");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">New client</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Basic info</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <Field label="Name" required>
              <Input
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="Acme Software"
                required
              />
            </Field>

            <Field
              label="Slug"
              hint="Lowercase, hyphens. Used in URLs."
              required
            >
              <Input
                value={form.slug}
                onChange={(e) => update("slug", e.target.value)}
                placeholder="acme-software"
                pattern="[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?"
                required
              />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field
                label="Google Ads CID"
                hint="10 digits. Add later if you don't have it."
              >
                <Input
                  value={form.google_ads_customer_id}
                  onChange={(e) => update("google_ads_customer_id", e.target.value)}
                  placeholder="1234567890"
                />
              </Field>
              <Field label="MCC login CID" hint="If you front via a Manager Account.">
                <Input
                  value={form.login_customer_id}
                  onChange={(e) => update("login_customer_id", e.target.value)}
                  placeholder="9876543210"
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Timezone">
                <Input
                  value={form.timezone}
                  onChange={(e) => update("timezone", e.target.value)}
                  placeholder="America/New_York"
                />
              </Field>
              <Field label="Currency">
                <Input
                  value={form.currency}
                  onChange={(e) => update("currency", e.target.value.toUpperCase())}
                  placeholder="USD"
                  maxLength={3}
                />
              </Field>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            <div className="flex gap-3">
              <Button type="submit" disabled={submitting}>
                {submitting ? "Creating…" : "Create client"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/clients")}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <div className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive"> *</span>}
      </div>
      {children}
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </label>
  );
}
