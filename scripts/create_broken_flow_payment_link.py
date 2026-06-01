"""Create Broken Flow Review ($49) Stripe product + Payment Link (idempotent).

Requires STRIPE_SECRET_KEY=sk_live_* in .env. Prints JSON with payment link URL.

    python scripts/create_broken_flow_payment_link.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")

PRODUCT_META = "broken_flow_review"
CENTS = 4900
SUCCESS_URL = "https://launchlook.app/thanks"
PROD_NAME = "Broken Flow Review"


def load_env() -> str:
    if not os.path.isfile(ENV_PATH):
        sys.exit(f"Missing {ENV_PATH}")
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_live"):
        sys.exit("Expected sk_live_* in STRIPE_SECRET_KEY")
    return key


def stripe_request(key: str, method: str, path: str, form: dict[str, str] | None = None):
    url = "https://api.stripe.com/v1/" + path
    data = urllib.parse.urlencode(form).encode("utf-8") if form else None
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "launchlook-create-broken-flow/1.0",
    }
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}


def list_all(key: str, path: str, params: dict[str, str] | None = None) -> list[dict]:
    items: list[dict] = []
    params = dict(params or {}, limit="100")
    starting_after = None
    while True:
        q = dict(params)
        if starting_after:
            q["starting_after"] = starting_after
        status, data = stripe_request(key, "GET", path + "?" + urllib.parse.urlencode(q))
        if status != 200:
            sys.exit(f"List {path} failed: {data}")
        items.extend(data["data"])
        if data.get("has_more"):
            starting_after = data["data"][-1]["id"]
        else:
            break
    return items


def find_existing_link(key: str) -> dict | None:
    links = list_all(key, "payment_links", {"active": "true"})
    links += list_all(key, "payment_links", {"active": "false"})
    for pl in links:
        if (pl.get("metadata") or {}).get("product") != PRODUCT_META:
            continue
        status, li = stripe_request(key, "GET", f"payment_links/{pl['id']}/line_items")
        if status != 200:
            continue
        for item in li.get("data", []):
            pr = item.get("price") or {}
            if pr.get("unit_amount") == CENTS:
                return pl
    return None


def main() -> int:
    key = load_env()
    existing = find_existing_link(key)
    if existing:
        print(
            json.dumps(
                {
                    "status": "already_exists",
                    "url": existing.get("url"),
                    "id": existing["id"],
                }
            )
        )
        return 0

    prod = None
    for p in list_all(key, "products", {"active": "true"}):
        if p.get("name") == PROD_NAME:
            prod = p
            break
    if not prod:
        status, prod = stripe_request(
            key,
            "POST",
            "products",
            {
                "name": PROD_NAME,
                "description": (
                    "Post-launch: one named failing flow, up to 5 findings "
                    "with paste-into-builder fix text."
                ),
                "metadata[sku]": PRODUCT_META,
            },
        )
        if status != 200:
            sys.exit(f"product create failed: {prod}")

    status, price = stripe_request(
        key,
        "POST",
        "prices",
        {
            "product": prod["id"],
            "unit_amount": str(CENTS),
            "currency": "usd",
            "nickname": "Broken Flow Review 49 USD",
            "metadata[sku]": PRODUCT_META,
        },
    )
    if status != 200:
        sys.exit(f"price create failed: {price}")

    status, link = stripe_request(
        key,
        "POST",
        "payment_links",
        {
            "line_items[0][price]": price["id"],
            "line_items[0][quantity]": "1",
            "after_completion[type]": "redirect",
            "after_completion[redirect][url]": SUCCESS_URL,
            "automatic_tax[enabled]": "false",
            "metadata[product]": PRODUCT_META,
        },
    )
    if status != 200:
        sys.exit(f"payment_link create failed: {link}")

    print(
        json.dumps(
            {
                "status": "created",
                "url": link.get("url"),
                "id": link["id"],
                "price_id": price["id"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
