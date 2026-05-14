# Data model

Postgres schema sketch. This is the proposed shape, not yet implemented — refine when scaffolding the API.

## Core entities

### `clients`
The agency's clients, each with one Google Ads CID (or MCC sub-CID).

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| name | text | |
| google_ads_customer_id | text | the CID without dashes |
| login_customer_id | text | parent MCC, if any |
| timezone | text | for "Monday 06:00 local" reports |
| currency | text | reporting currency |
| created_at | timestamptz | |
| active | bool | |

### `playbooks`
Per-client playbook content, versioned.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| version | int | monotonically increasing |
| content_md | text | the markdown |
| parsed | jsonb | extracted structured fields (see schema below) |
| created_by | uuid fk users | |
| created_at | timestamptz | |

Parsed playbook schema:
```json
{
  "icp": "string",
  "sales_cycle_days": 84,
  "acv_usd": 25000,
  "target_cac_usd": 5000,
  "target_ltv_cac_ratio": 3.0,
  "conversion_hierarchy": [
    {"name": "SQL", "value_usd": 50, "primary": false},
    {"name": "Opportunity", "value_usd": 500, "primary": false},
    {"name": "Closed_Won", "value_usd": 25000, "primary": true}
  ],
  "required_campaign_archetypes": ["Brand", "Competitor", "NonBrandProduct", "NonBrandProblem", "Remarketing"],
  "bidding_rules": [
    "No broad match until OCI flowing for 30+ days",
    "Target CPA cap must be set on Max Conversions strategies",
    "Conversion window must be >= 90 days for primary actions"
  ],
  "negative_overlays": ["competitor_employees:[list]", "client_specific:[list]"],
  "brand_voice": {
    "tone": "professional, direct, data-driven",
    "banned_phrases": ["revolutionary", "synergy", "game-changer"],
    "required_disclaimers": []
  },
  "approval_thresholds": {
    "auto_approve_l1_under_usd": 50,
    "require_mfa_above_usd": 500
  },
  "oci_sheet_id": "1AbC...",
  "auto_apply_recommendations_should_be": "off",
  "search_partners_should_be": "off"
}
```

### `accounts_snapshot`
Daily snapshot of an account-level state. Append-only.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| snapshot_date | date | |
| optimization_score | numeric | |
| auto_apply_settings | jsonb | which recommendation types are auto-applied |
| primary_conversion_action_count | int | |
| ec4l_enabled | bool | |
| ... | | |

### `campaigns`, `ad_groups`, `keywords`, `ads`, `assets`
Mirror of Google Ads entities. Soft-deletes; we keep history of removed entities for audit purposes.

### `metrics_daily`
Granular metric storage, partitioned by month.

| col | type | notes |
|---|---|---|
| client_id | uuid | |
| entity_type | text | enum: campaign / ad_group / keyword / search_term / ad / asset |
| entity_id | text | Google Ads resource id |
| date | date | partition key |
| impressions | int | |
| clicks | int | |
| cost_micros | bigint | |
| conversions | numeric | |
| conversions_value | numeric | |
| all_conversions | numeric | |
| view_through_conversions | numeric | |
| dimensions | jsonb | device, network, etc. when applicable |

### `change_events`
From Google Ads `change_event` API + our own writes.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| event_time | timestamptz | |
| source | text | enum: google_ads / our_action_queue / unknown |
| changed_resource | text | resource name |
| change_type | text | created / updated / removed |
| user_email | text | who, if known |
| old_resource | jsonb | |
| new_resource | jsonb | |
| associated_action_id | uuid fk actions | nullable, set when we wrote it |

### `actions`
The Action Queue spine.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| type | text | enum: pause_campaign / add_negative / change_budget / upload_oci / edit_rsa_asset / pause_keyword / change_target_cpa / disable_auto_apply / ... |
| target | jsonb | { resource_name, level, name } |
| diff | jsonb | { before, after } |
| reasoning_md | text | Claude's structured explanation |
| evidence | jsonb | sample data referenced |
| expected_impact | jsonb | { metric, delta, confidence_pct } |
| risk_tier | text | L1 / L2 / L3 |
| status | text | proposed / approved / rejected / executed / failed / expired |
| approver_id | uuid fk users | |
| approved_at | timestamptz | |
| executed_at | timestamptz | |
| execution_result | jsonb | API response or error |
| created_at | timestamptz | |
| expires_at | timestamptz | proposals auto-expire after 30 days |

### `audits`
A point-in-time audit run.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| run_at | timestamptz | |
| overall_score | numeric | 0–100 |
| grade | text | A / B / C / D / F |
| category_scores | jsonb | per category |
| created_by | uuid fk users | nullable for scheduled runs |

### `audit_check_results`
One row per check executed in an audit.

| col | type | notes |
|---|---|---|
| audit_id | uuid fk | |
| check_id | text | stable identifier (e.g. `tracking.conversion_window_lt_90d`) |
| passed | bool | |
| severity | text | critical / high / medium / low |
| weight | numeric | |
| evidence | jsonb | what failed and how |
| suggested_fix_md | text | |
| draft_action_id | uuid fk actions | nullable |

### `oci_uploads`
Track every OCI batch.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| source | text | google_sheet / hubspot / salesforce / manual |
| uploaded_at | timestamptz | |
| total_rows | int | |
| accepted | int | |
| rejected | int | |
| errors | jsonb | per-row error summary |

### `users`
Agency staff.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| email | text | |
| name | text | |
| role | text | admin / strategist / analyst |
| google_oauth_tokens | jsonb | |
| mfa_method | text | totp / webauthn |
| client_access | jsonb | [{ client_id, level }] |

### `report_runs`
Weekly/monthly report deliveries.

| col | type | notes |
|---|---|---|
| id | uuid pk | |
| client_id | uuid fk | |
| period | text | weekly / monthly |
| period_start | date | |
| period_end | date | |
| html | text | |
| pdf_r2_key | text | nullable |
| llm_model | text | |
| llm_input_tokens | int | |
| llm_output_tokens | int | |
| llm_cost_usd | numeric | |
| delivered_to | text[] | email addresses |
| created_at | timestamptz | |

## Indexes worth planning early

- `metrics_daily(client_id, entity_type, entity_id, date desc)` — primary lookup
- `metrics_daily` partitioned monthly
- `actions(client_id, status, created_at desc)` — queue display
- `change_events(client_id, event_time desc)` — change-history view
- `playbooks(client_id, version desc)` — current playbook fetch
- `audit_check_results(audit_id, severity, weight desc)` — audit drill-down

## What we do NOT store

- Raw user PII from CRM beyond hashed email/phone for EC4L (per Google's hashing requirement)
- Client passwords (OAuth tokens only)
- Credit card data
- The raw bodies of competitor ad creatives (links only — copyright/ToS caution)
