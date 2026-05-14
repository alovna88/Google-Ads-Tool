// API client. Browser always hits same-origin `/api/*` (Next.js rewrites
// proxy it to the FastAPI server). Server components in production can
// hit the API directly via API_INTERNAL_URL to skip the proxy hop.

const BROWSER_BASE = "/api";
const SERVER_BASE =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

function resolveBase(): string {
  return typeof window === "undefined" ? SERVER_BASE : BROWSER_BASE;
}

export type Client = {
  id: string;
  name: string;
  slug: string;
  google_ads_customer_id: string | null;
  login_customer_id: string | null;
  timezone: string;
  currency: string;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type ClientList = {
  items: Client[];
  total: number;
};

export type Playbook = {
  id: string;
  client_id: string;
  version: number;
  content_md: string;
  parsed: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CurrentUser = {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
};

class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API ${status}`);
  }
}

async function request<T>(
  path: string,
  init?: RequestInit & { cookie?: string },
): Promise<T> {
  // On the server we have to forward the incoming Cookie header for
  // session-aware calls; the browser sends cookies automatically when
  // we use `credentials: 'include'`.
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (init?.cookie) headers["Cookie"] = init.cookie;

  const res = await fetch(`${resolveBase()}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // Auth
  me: (opts?: { cookie?: string }) => request<CurrentUser>("/auth/me", opts),
  logout: () => request<void>("/auth/logout", { method: "POST" }),

  // Clients
  listClients: (opts?: { cookie?: string }) =>
    request<ClientList>("/clients", opts),
  getClient: (id: string, opts?: { cookie?: string }) =>
    request<Client>(`/clients/${id}`, opts),
  createClient: (payload: Partial<Client>) =>
    request<Client>("/clients", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Playbooks
  getPlaybook: (clientId: string, opts?: { cookie?: string }) =>
    request<Playbook>(`/clients/${clientId}/playbook`, opts),
  savePlaybook: (clientId: string, contentMd: string) =>
    request<Playbook>(`/clients/${clientId}/playbook`, {
      method: "PUT",
      body: JSON.stringify({ content_md: contentMd }),
    }),
};

export { ApiError };
