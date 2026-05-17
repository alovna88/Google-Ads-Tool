import Link from "next/link";
import type { CurrentUser } from "@/lib/api";
import { UserMenu } from "./user-menu";

export function Nav({ user }: { user: CurrentUser | null }) {
  return (
    <nav className="border-b border-border bg-background">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="font-semibold tracking-tight">
          Agency Google Ads
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link href="/clients" className="text-muted-foreground hover:text-foreground">
            Clients
          </Link>
          <Link href="/queue" className="text-muted-foreground hover:text-foreground">
            Action Queue
          </Link>
          <span className="text-muted-foreground/50" title="Coming next">
            Reports
          </span>
          {user && <UserMenu user={user} />}
        </div>
      </div>
    </nav>
  );
}
