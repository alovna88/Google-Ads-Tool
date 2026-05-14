import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-4 text-center">
      <h1 className="text-2xl font-semibold">Client not found</h1>
      <p className="text-muted-foreground">
        That client doesn&apos;t exist or you don&apos;t have access.
      </p>
      <Link href="/clients" className="underline">
        Back to clients
      </Link>
    </div>
  );
}
