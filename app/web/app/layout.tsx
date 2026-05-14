import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Nav } from "@/components/nav";
import { getCurrentUser } from "@/lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agency Google Ads",
  description: "Internal Google Ads agency tool",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const headerList = await headers();
  const pathname = headerList.get("x-pathname") ?? "";
  const isAuthPage = pathname.startsWith("/login");

  let user = null;
  if (!isAuthPage) {
    user = await getCurrentUser();
    // Middleware checks cookie presence only; if a stale cookie slipped
    // through, /auth/me returned null and we bounce to /login here.
    if (!user) {
      redirect(`/login?next=${encodeURIComponent(pathname || "/")}`);
    }
  }

  return (
    <html lang="en">
      <body>
        {!isAuthPage && <Nav user={user} />}
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
