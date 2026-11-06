"""Free GET-only OpenRouter readiness check; never loads .env or invokes a model."""
import argparse
import json
import os
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def fetch(path, key=None):
    request = Request("https://openrouter.ai/api/v1/" + path,
                      headers={"Authorization": "Bearer " + key} if key else {})
    with urlopen(request, timeout=30) as response:
        return json.load(response)["data"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-only", action="store_true", help="Skip the optional authenticated key GET")
    args = parser.parse_args()
    print("Before any cohort: python scripts/check_tool_schemas.py (offline), then --live (one paid request; explicit approval required). Metadata support alone does not prove schema acceptance.")
    model_id = os.environ.get("OPENROUTER_CHAT_MODEL", "").strip() or "google/gemini-3.6-flash"
    try:
        model = next((m for m in fetch("models") if m["id"] == model_id), None)
        if model is None:
            print("FAIL: configured model is missing")
            return 1
        if not {"tools", "tool_choice"} <= set(model.get("supported_parameters", [])):
            print("FAIL: model lacks tools/tool_choice support")
            return 1
        print(f"Model: {model_id}; tools + tool_choice: supported")
        for name in ("prompt", "completion"):
            price = Decimal(model["pricing"][name]) * 1_000_000
            print(f"{name}: USD {price:f} per million tokens")
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if key and not args.models_only:
            data = fetch("key", key)
            print(f"Credit USD: limit={data.get('limit')}; usage={data.get('usage')}; remaining={data.get('limit_remaining')}")
        else:
            print("Key check skipped (models only or no process key)")
        return 0
    except (HTTPError, URLError, ValueError, KeyError):
        print("FAIL: OpenRouter readiness GET failed (credentials and response bodies suppressed)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
