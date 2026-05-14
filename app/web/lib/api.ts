// API client. Server-side requests go directly to API_BASE_URL_INTERNAL
// (the in-cluster service URL); client-side requests go through the public
// NEXT_PUBLIC_API_BASE_URL. We always use the public one in this scaffold
// because both server-component and client-component fetches need a URL the
// container network can resolve.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// In Docker Compose, server components can't reach `localhost` (that's the
// container's own loopback). The compose file sets this only at runtime.
const API_BASE_URL_INTERNAL =
  process.env.API_BASE_URL_INTERNAL ?? API_BASE_URL;

function resolveBase(): string {
  return typeof window === "undefined" ? API_BASE_URL_INTERNAL : API_BASE_URL;
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

class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${resolveBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listClients: () => request<ClientList>("/clients"),
  getClient: (id: string) => request<Client>(`/clients/${id}`),
  createClient: (payload: Partial<Client>) =>
    request<Client>("/clients", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getPlaybook: (clientId: string) =>
    request<Playbook>(`/clients/${clientId}/playbook`),
  savePlaybook: (clientId: string, contentMd: string) =>
    request<Playbook>(`/clients/${clientId}/playbook`, {
      method: "PUT",
      body: JSON.stringify({ content_md: contentMd }),
    }),
};

export { ApiError };
