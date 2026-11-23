#!/usr/bin/env python3
"""Hammer /health (no auth) and /v1/me/summary to demonstrate rate limiting."""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Locked-In rate-limit load test")
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=50, help="Number of authenticated requests")
    parser.add_argument(
        "--api-key",
        default=os.getenv("API_KEY", "dev-secret-change-me"),
    )
    args = parser.parse_args()

    ok = 0
    limited = 0
    other = 0
    headers = {"x-api-key": args.api_key}
    started = time.perf_counter()

    with httpx.Client(timeout=10.0) as client:
        health = client.get(f"{args.base}/health")
        print(f"health {health.status_code} {health.json()}")

        for i in range(args.n):
            response = client.get(f"{args.base}/v1/me/summary", headers=headers)
            if response.status_code == 200:
                ok += 1
            elif response.status_code == 429:
                limited += 1
                if limited == 1:
                    print(
                        f"first 429 at request {i + 1}; "
                        f"Retry-After={response.headers.get('Retry-After')} "
                        f"body={response.json()}"
                    )
            else:
                other += 1
                print(f"unexpected {response.status_code}: {response.text[:200]}")

    elapsed = time.perf_counter() - started
    print(
        f"done in {elapsed:.2f}s — 200={ok} 429={limited} other={other} "
        f"(limit should trip after RATE_LIMIT_REQUESTS)"
    )
    return 0 if limited > 0 or ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
