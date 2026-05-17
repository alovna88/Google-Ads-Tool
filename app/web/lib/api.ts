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

export type AuditSummary = {
  id: string;
  run_at: string;
  overall_score: number;
  grade: string;
};

export type AuditCheckResult = {
  id: string;
  check_id: string;
  category: string;
  title: string;
  passed: boolean;
  severity: "critical" | "high" | "medium" | "low";
  weight: number;
  evidence: Record<string, unknown>;
  suggested_fix_md: string | null;
  draft_action_id: string | null;
};

export type Audit = {
  id: string;
  client_id: string;
  run_at: string;
  overall_score: number;
  grade: string;
  category_scores: Record<string, { score: number; grade: string }>;
  check_results: AuditCheckResult[];
};

export type AuditList = {
  items: AuditSummary[];
  total: number;
};

export type ActionStatus =
  | "proposed"
  | "approved"
  | "rejected"
  | "executed"
  | "failed"
  | "expired";

export type Action = {
  id: string;
  client_id: string;
  audit_id: string | null;
  type: string;
  target: Record<string, unknown>;
  diff: Record<string, unknown>;
  reasoning_md: string;
  evidence: Record<string, unknown>;
  expected_impact: Record<string, unknown>;
  risk_tier: "L1" | "L2" | "L3";
  status: ActionStatus;
  approver_id: string | null;
  approved_at: string | null;
  executed_at: string | null;
  execution_result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  client_name: string;
  client_slug: string;
};

export type ActionList = {
  items: Action[];
  total: number;
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

  // Audits
  listClientAudits: (clientId: string, opts?: { cookie?: string }) =>
    request<AuditList>(`/clients/${clientId}/audits`, opts),
  runAudit: (clientId: string, snapshot?: Record<string, unknown> | null) =>
    request<Audit>(`/clients/${clientId}/audits`, {
      method: "POST",
      body: JSON.stringify({ snapshot: snapshot ?? null }),
    }),
  getAudit: (auditId: string, opts?: { cookie?: string }) =>
    request<Audit>(`/audits/${auditId}`, opts),

  // Actions
  listActions: (
    opts?: { cookie?: string; status?: string; clientId?: string },
  ) => {
    const params = new URLSearchParams();
    if (opts?.status) params.set("status", opts.status);
    if (opts?.clientId) params.set("client_id", opts.clientId);
    const qs = params.toString();
    return request<ActionList>(`/actions${qs ? `?${qs}` : ""}`, opts);
  },
  patchAction: (id: string, transition: "approve" | "reject") =>
    request<Action>(`/actions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ transition }),
    }),
};

export { ApiError };
