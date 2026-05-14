import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Agency Google Ads</h1>
        <p className="mt-2 text-muted-foreground">
          Internal tool for managing the portfolio. The skills pack works today; the
          web app is being built in phases.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Clients</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Manage the client portfolio. Connect MCC, edit per-client playbooks.
            </p>
            <Link
              href="/clients"
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              Open clients →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>What ships next</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>· Staff Google OAuth login</li>
              <li>· Google Ads MCC connection per client</li>
              <li>· Nightly read sync via GAQL</li>
              <li>· Action Queue with draft / approve / push</li>
              <li>· Audit engine + weighted A–F score</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
