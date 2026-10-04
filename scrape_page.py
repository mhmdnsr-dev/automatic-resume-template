#!/usr/bin/env python3
"""
Scrape title + main text from a public (no-auth) URL via playwright-cli.

Usage:
  python scrape_page.py "https://example.com/job/..."
  python scrape_page.py "https://..." -o path\\to\\jd.txt
  python scrape_page.py "https://..." --stdout

Requires: playwright-cli on PATH (npm i -g @playwright/cli)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LOGIN_WALL_PATTERNS = (
    r"\bsign[\s-]?in\b",
    r"\blog[\s-]?in\b",
    r"\bauthwall\b",
    r"\bjoin\s+linkedin\b",
    r"\bcreate\s+an\s+account\b",
    r"\bauthenticate\b",
    r"\bsession\s+expired\b",
)

EXTRACT_JS = (
    "() => {"
    " const root = document.querySelector('article')"
    "  || document.querySelector('[role=\"main\"]')"
    "  || document.querySelector('main')"
    "  || document.body;"
    " if (!root) return { title: (document.title||'').trim(), url: location.href, text: '' };"
    " const clone = root.cloneNode(true);"
    " clone.querySelectorAll('script,style,noscript,svg,iframe').forEach(el => el.remove());"
    " const text = (clone.innerText || clone.textContent || '')"
    "  .replace(/\\r/g,'').replace(/[ \\t]+\\n/g,'\\n').replace(/\\n{3,}/g,'\\n\\n').trim();"
    " return { title: (document.title||'').trim(), url: location.href, text: text };"
    "}"
)


def find_cli() -> str:
    path = shutil.which("playwright-cli")
    if path:
        return path
    raise RuntimeError(
        "playwright-cli not found on PATH.\n"
        "Install: npm install -g @playwright/cli@latest\n"
        "Then: playwright-cli install-browser chromium"
    )


def run_cli(cli: str, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [cli, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=str(ROOT),
    )


def parse_eval_payload(stdout: str) -> dict:
    """Parse playwright-cli eval output (raw JSON string or --json wrapper)."""
    raw = stdout.strip()
    if not raw:
        raise RuntimeError("playwright-cli eval returned empty output")

    # --json form: {"result": { ... }} or {"result": "{ ... }"} or {"isError": true, ...}
    try:
        outer = json.loads(raw)
        if isinstance(outer, dict) and outer.get("isError"):
            raise RuntimeError(outer.get("error") or raw)
        if isinstance(outer, dict) and "result" in outer:
            result = outer["result"]
            if isinstance(result, str):
                # Sometimes CLI stringifies objects
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    return {"title": "", "url": "", "text": result}
            if isinstance(result, dict):
                return result
    except json.JSONDecodeError:
        pass

    # --raw form: bare JSON object/string
    try:
        data = json.loads(raw)
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, dict):
            if data.get("isError"):
                raise RuntimeError(data.get("error") or raw)
            return data
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse eval output:\n{raw[:500]}") from exc

    raise RuntimeError(f"Unexpected eval payload:\n{raw[:500]}")


def looks_like_login_wall(title: str, text: str) -> bool:
    sample = f"{title}\n{text[:2000]}".lower()
    return any(re.search(pat, sample, re.I) for pat in LOGIN_WALL_PATTERNS)


def scrape(url: str) -> dict:
    cli = find_cli()
    opened = False
    try:
        # Clear stale sessions so open/eval share a fresh browser.
        run_cli(cli, ["close-all"], timeout=30)

        open_res = run_cli(cli, ["open", url], timeout=180)
        if open_res.returncode != 0:
            raise RuntimeError(
                f"playwright-cli open failed (exit {open_res.returncode}):\n"
                f"{open_res.stderr or open_res.stdout}"
            )
        opened = True

        # Ensure navigation finished / DOM ready.
        run_cli(
            cli,
            ["--raw", "eval", "() => document.readyState"],
            timeout=30,
        )

        eval_res = run_cli(cli, ["--json", "eval", EXTRACT_JS], timeout=60)
        combined = (eval_res.stdout or "") + "\n" + (eval_res.stderr or "")
        if eval_res.returncode != 0:
            raise RuntimeError(
                f"playwright-cli eval failed (exit {eval_res.returncode}):\n{combined}"
            )

        data = parse_eval_payload(eval_res.stdout or eval_res.stderr)
        title = (data.get("title") or "").strip()
        final_url = (data.get("url") or url).strip()
        text = (data.get("text") or "").strip()

        if not text:
            raise RuntimeError(
                "Scraped page body is empty. The URL may require authentication "
                "or block bots. Paste the content into jd.txt manually.\n"
                f"Debug eval output:\n{(eval_res.stdout or '')[:800]}"
            )

        if looks_like_login_wall(title, text) and len(text) < 800:
            raise RuntimeError(
                "Page looks like a login / auth wall (public scrape not possible).\n"
                "Paste the job description into jd.txt manually."
            )

        return {"title": title, "url": final_url, "text": text}
    finally:
        if opened:
            try:
                run_cli(cli, ["close"], timeout=30)
            except Exception:
                pass
        try:
            run_cli(cli, ["close-all"], timeout=30)
        except Exception:
            pass


def format_output(data: dict) -> str:
    return (
        f"URL: {data['url']}\n"
        f"Title: {data['title']}\n"
        f"\n"
        f"{data['text']}\n"
    )


def default_out_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / f"scraped_{stamp}.txt"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Scrape a public page (no auth) via playwright-cli into plain text."
    )
    parser.add_argument("url", help="Public page URL")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: scraped_<timestamp>.txt in repo root)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print scraped text to stdout instead of writing a file",
    )
    args = parser.parse_args(argv[1:])

    try:
        data = scrape(args.url)
        body = format_output(data)
        if args.stdout:
            sys.stdout.write(body)
            return 0

        out = Path(args.output) if args.output else default_out_path()
        if not out.is_absolute():
            out = (ROOT / out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        print(f"Wrote: {out}", flush=True)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
