"""AccountSnapshot — the structured payload checks read from.

In production this will be assembled by the daily Google Ads sync from
GAQL responses. For now we accept it as JSON via the audit endpoint, and
fall back to a built-in fixture so demos work without a live account.

Shape (informal — checks consume the dict directly):

    {
      "conversion_actions": [
        {
          "name": "Lead form",
          "primary": true,
          "category": "LEAD",
          "click_through_window_days": 30,
          "value_settings": {"default_value": 0, "always_use_default": true}
        }
      ],
      "auto_apply": {
        "enabled_types": ["ADD_RESPONSIVE_SEARCH_AD", "USE_DISPLAY_EXPANSION"]
      },
      "campaigns": [
        {
          "id": "1234",
          "name": "Brand",
          "type": "SEARCH",
          "status": "ENABLED",
          "include_display_network": false,
          "search_partners_enabled": true,
          "bidding_strategy": "MAXIMIZE_CONVERSIONS",
          "target_cpa_micros": null,
          "target_roas": null
        }
      ],
      "metrics_30d": {
        "campaign_id_to_conversions": {"1234": 12}
      }
    }
"""

from typing import Any


DEMO_SNAPSHOT: dict[str, Any] = {
    "conversion_actions": [
        {
            "name": "Lead form submit",
            "primary": True,
            "category": "LEAD",
            "click_through_window_days": 30,
            "view_through_window_days": 1,
            "value_settings": {"default_value": 0, "always_use_default": True},
        },
        {
            "name": "SQL (offline)",
            "primary": False,
            "category": "LEAD",
            "click_through_window_days": 90,
            "view_through_window_days": 1,
            "value_settings": {"default_value": 50, "always_use_default": False},
        },
    ],
    "auto_apply": {
        "enabled_types": [
            "ADD_RESPONSIVE_SEARCH_AD",
            "USE_DISPLAY_EXPANSION",
            "USE_BROAD_MATCH_KEYWORD",
        ],
    },
    "campaigns": [
        {
            "id": "100001",
            "name": "Brand · Exact",
            "type": "SEARCH",
            "status": "ENABLED",
            "include_display_network": True,
            "search_partners_enabled": True,
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "target_cpa_micros": None,
            "target_roas": None,
        },
        {
            "id": "100002",
            "name": "Non-brand · Product",
            "type": "SEARCH",
            "status": "ENABLED",
            "include_display_network": False,
            "search_partners_enabled": True,
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "target_cpa_micros": 200_000_000,
            "target_roas": None,
        },
    ],
    "metrics_30d": {
        "campaign_id_to_conversions": {"100001": 22, "100002": 18},
    },
}


def coerce_snapshot(value: dict[str, Any] | None) -> dict[str, Any]:
    """Return a usable snapshot. Falls back to DEMO_SNAPSHOT if `value`
    is empty/None — the audit engine will run without a live account.
    """
    if not value:
        return DEMO_SNAPSHOT
    # Future: validate against a Pydantic model. For now we accept any
    # dict — checks defensively read with .get() and skip when fields
    # are missing.
    return value
