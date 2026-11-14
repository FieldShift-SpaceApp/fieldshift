# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Step 5. ENSO Alert System status in the NOAA CPC ENSO Diagnostic Discussions, Mar-Jun 2023.

Usage: python -I cpc_alerts_2023.py <results_dir>
Writes cpc_alerts_2023.json with issue date, alert status and synopsis sentence of each month.
"""

import html
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_disc_{m}2023/ensodisc.shtml"


def text(h: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"\s+", " ", t)


def get_text(client: httpx.Client, url: str) -> str:
    for attempt in range(4):
        try:
            return client.get(url).raise_for_status().text
        except httpx.HTTPError as e:
            print(f"attempt {attempt + 1} failed for {url}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"giving up on {url}")


def main() -> None:
    out = []
    with httpx.Client(timeout=60, headers={"User-Agent": "fieldshift-analysis/1.0"}) as client:
        for m in ("mar", "apr", "may", "jun"):
            url = URL.format(m=m)
            t = text(get_text(client, url))
            issued = re.search(r"issued by .*?(\d{1,2} \w+ 2023)", t)
            status = re.search(r"ENSO Alert System Status:\s*(.+?)\s+Synopsis", t)
            synopsis = re.search(r"Synopsis:\s*(.+?\.)\s", t)
            out.append(
                {
                    "url": url,
                    "accessed_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "issued": issued.group(1) if issued else None,
                    "status": status.group(1).strip() if status else None,
                    "synopsis": synopsis.group(1).strip() if synopsis else None,
                }
            )
    path = Path(sys.argv[1], "cpc_alerts_2023.json")
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for o in out:
        print(o["issued"], "|", o["status"], "|", o["synopsis"])


if __name__ == "__main__":
    main()
