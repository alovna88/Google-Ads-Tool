"use client";

import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const ERROR_MESSAGES: Record<string, string> = {
  not_allowed: "That email isn't on the agency allowlist. Ask an admin to add it.",
  email_not_verified: "Your Google email isn't verified.",
  state_mismatch: "Login was interrupted — please try again.",
  state_invalid: "Login session expired — please try again.",
  oauth_denied: "Login was cancelled.",
  missing_code: "Login failed — no authorization code returned.",
  token_exchange_failed: "Couldn't complete the login with Google.",
  provider_error: "Couldn't reach Google to complete login. Try again shortly.",
};

export function LoginForm() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const next = searchParams.get("next") ?? "/";

  function startLogin() {
    const url = `/api/auth/login?next=${encodeURIComponent(next)}`;
    window.location.href = url;
  }

  return (
    <Card>
      <CardContent className="space-y-6 p-8">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">
            Agency Google Ads
          </h1>
          <p className="text-sm text-muted-foreground">
            Sign in with your agency Google account to continue.
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {ERROR_MESSAGES[error] ?? `Login error: ${error}`}
          </div>
        )}

        <Button className="w-full" onClick={startLogin}>
          Continue with Google
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          Internal tool. Access is restricted to allow-listed emails.
        </p>
      </CardContent>
    </Card>
  );
}
