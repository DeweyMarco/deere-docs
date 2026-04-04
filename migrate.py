#!/usr/bin/env python3
"""
Page Migration Script — URL → MDX + OpenAPI
--------------------------------------------
Reads a list of URLs from urls.txt (one per line), fetches each page,
and uses Claude Code (claude -p) to generate:
  1. A Mintlify-compatible MDX file
  2. An OpenAPI 3.0 JSON spec

Usage:
  python migrate.py

Requirements:
  pip install requests beautifulsoup4
  claude  (Claude Code CLI, already authenticated)

Configuration:
  - Edit urls.txt with one URL per line (lines starting with # are ignored)
  - Edit OUTPUT_DIR to match your project structure
"""

import os
import json
import re
import sys
import time
import textwrap
from pathlib import Path
from urllib.parse import urlparse

# ── Configuration ────────────────────────────────────────────────────────────

MODEL = "claude-opus-4-6"  # or "claude-sonnet-4-6" for faster/cheaper runs

URLS_FILE = Path(__file__).parent / "urls.txt"
MDX_OUTPUT_DIR = Path(__file__).parent          # MDX files go here (organised by slug)
OPENAPI_OUTPUT_DIR = Path(__file__).parent / "openapi"  # OpenAPI JSONs go here

# Seconds to wait between API calls to avoid rate limits
RATE_LIMIT_DELAY = 2

# ── MDX example (from your repo) ─────────────────────────────────────────────

MDX_EXAMPLE = """---
title: "Merchant Transactions API"
description: "Submit and manage transactions for John Deere Financial revolving finance products."
---

## Overview

The Merchant Transactions API facilitates transaction processing for John Deere Financial merchants.

<Note>
  This API is intended for entities that provide Business Systems connected with registered merchants.
</Note>

<CardGroup cols={2}>
  <Card title="Authorizations" icon="shield-check">
    Reserve credit on a customer's account before a purchase is finalized.
  </Card>
  <Card title="Captures" icon="circle-check">
    Consume a previously reserved authorization when a purchase is finalized.
  </Card>
</CardGroup>

---

## Authentication

<Steps>
  <Step title="Create an application">
    Your application will be assigned a **Client Key** and **Client Secret**.
  </Step>
  <Step title="Acquire an access token">
    POST to the token endpoint with your credentials.
  </Step>
  <Step title="Call the API">
    ```bash
    Authorization: Bearer <access_token>
    ```
  </Step>
</Steps>

---

## Endpoints

### Create a Resource

```
POST /resource
```

<ParamField body="accountNumber" type="string" required>
  Customer's account number.
</ParamField>

<ParamField body="amount" type="number" required>
  Amount in USD.
</ParamField>

<Card title="Try it in the API Playground" icon="play" href="/POST /resource">
  Test this endpoint interactively.
</Card>
"""

OPENAPI_EXAMPLE = """{
  "openapi": "3.0.0",
  "info": {
    "title": "Merchant Transactions API",
    "description": "Facilitates transaction processing for John Deere Financial merchants.",
    "version": "1.0.0"
  },
  "servers": [{ "url": "https://sandbox-api.example.com", "description": "Sandbox" }],
  "components": {
    "securitySchemes": {
      "OAuth2": {
        "type": "oauth2",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://auth.example.com/authorize",
            "tokenUrl": "https://auth.example.com/token",
            "scopes": { "offline_access": "Request a Refresh Token" }
          }
        }
      }
    },
    "schemas": {
      "ExampleRequest": {
        "type": "object",
        "required": ["accountNumber", "amount"],
        "properties": {
          "accountNumber": { "type": "string", "example": "1234567890" },
          "amount": { "type": "number", "example": 100.00 }
        }
      }
    }
  },
  "paths": {
    "/resource": {
      "post": {
        "summary": "Create a resource",
        "operationId": "createResource",
        "security": [{ "OAuth2": [] }],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ExampleRequest" }
            }
          }
        },
        "responses": {
          "200": { "description": "Success" },
          "400": { "description": "Bad Request" },
          "401": { "description": "Unauthorized" }
        }
      }
    }
  }
}"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def url_to_slug(url: str) -> str:
    """Derive a slug from the URL path."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        path = parsed.netloc.replace(".", "-")
    return slugify(path.replace("/", "-"))

def fetch_page(url: str) -> str:
    """Fetch a URL and return its text content, stripping most HTML."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Missing dependencies. Run: pip install requests beautifulsoup4")
        sys.exit(1)

    headers = {"User-Agent": "Mozilla/5.0 (compatible; migration-bot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "head", "noscript", "svg", "img"]):
        tag.decompose()

    # Try to grab main content first
    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.body
    text = main.get_text(separator="\n") if main else soup.get_text(separator="\n")

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text[:30000]  # Truncate to avoid token limits

def call_claude(prompt: str, system: str) -> str:
    """Call Claude Code CLI (claude -p) and return the text response."""
    import subprocess

    full_prompt = f"{system.strip()}\n\n---\n\n{prompt.strip()}"

    result = subprocess.run(
        ["claude", "-p", "--model", MODEL, full_prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    return result.stdout.strip()

def generate_mdx(page_content: str, url: str) -> str:
    """Generate a Mintlify MDX file from raw page content."""
    system = textwrap.dedent(f"""
        You are a technical writer converting web pages into Mintlify MDX documentation files.

        OUTPUT RULES:
        - Output ONLY the raw MDX file content — no markdown fences, no explanation
        - Start with frontmatter: --- title: "..." description: "..." ---
        - Use Mintlify components: <Note>, <Warning>, <CardGroup cols={{2}}>, <Card title="" icon="" href="">,
          <Steps>, <Step title="">, <ParamField body/path/query="" type="" required>, <CodeGroup>
        - Use ```bash, ```json, ```python code blocks inside <CodeGroup> when showing multi-language examples
        - Organize with ## and ### headings; use --- horizontal rules between major sections
        - For API endpoints: show the HTTP method + path in a code block, then list params with <ParamField>
        - For each endpoint, add: <Card title="Try it in the API Playground" icon="play" href="/METHOD /path">
        - Keep prose tight and technical — no marketing fluff
        - Do NOT invent information not present in the source page

        REFERENCE EXAMPLE (match this style exactly):
        {MDX_EXAMPLE}
    """)

    prompt = f"Convert this page from {url} into a Mintlify MDX file:\n\n{page_content}"
    return call_claude(prompt, system)

def generate_openapi(page_content: str, url: str, mdx_content: str) -> dict:
    """Generate an OpenAPI 3.0 JSON spec from raw page content."""
    system = textwrap.dedent(f"""
        You are an API documentation engineer converting web pages into OpenAPI 3.0.0 JSON specs.

        OUTPUT RULES:
        - Output ONLY valid JSON — no markdown fences, no explanation, no trailing commas
        - Always include: openapi, info (title, description, version), servers, components (securitySchemes, schemas), paths
        - Use OAuth2 authorizationCode flow for auth unless the page clearly uses something else
        - Define reusable schemas in components/schemas and reference them with $ref
        - For each endpoint include: summary, operationId, security, requestBody (if applicable), parameters, responses
        - Include at least 200, 400, and 401 responses for each endpoint
        - Add realistic example values to all schema properties
        - Do NOT invent endpoints not present in the source — only document what you see

        REFERENCE EXAMPLE (match this structure):
        {OPENAPI_EXAMPLE}
    """)

    prompt = textwrap.dedent(f"""
        Convert this API documentation into an OpenAPI 3.0 JSON spec.

        Source URL: {url}

        Page content:
        {page_content}

        Already-generated MDX (use as additional context):
        {mdx_content[:4000]}
    """)

    raw = call_claude(prompt, system)

    # Strip any accidental markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"\n?```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  OpenAPI JSON parse error: {e}")
        print("  Raw output saved to debug_openapi.txt")
        Path("debug_openapi.txt").write_text(raw)
        return {}

def save_mdx(content: str, slug: str) -> Path:
    MDX_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = MDX_OUTPUT_DIR / f"{slug}.mdx"
    path.write_text(content, encoding="utf-8")
    return path

def save_openapi(spec: dict, slug: str) -> Path:
    OPENAPI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OPENAPI_OUTPUT_DIR / f"{slug}.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return path

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Check that Claude Code CLI is available
    import subprocess
    check = subprocess.run(["which", "claude"], capture_output=True)
    if check.returncode != 0:
        print("❌  Claude Code CLI not found. Make sure 'claude' is installed and on your PATH.")
        sys.exit(1)

    if not URLS_FILE.exists():
        print(f"❌  {URLS_FILE} not found. Create it with one URL per line.")
        sys.exit(1)

    urls = [
        line.strip()
        for line in URLS_FILE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not urls:
        print("❌  urls.txt is empty or has no valid URLs.")
        sys.exit(1)

    print(f"🚀  Migrating {len(urls)} page(s)...\n")

    for i, url in enumerate(urls, 1):
        slug = url_to_slug(url)
        print(f"[{i}/{len(urls)}] {url}")
        print(f"       slug: {slug}")

        # 1. Fetch
        print("       fetching page...", end=" ", flush=True)
        try:
            page_content = fetch_page(url)
            print("✓")
        except Exception as e:
            print(f"✗ ({e})")
            continue

        # 2. MDX
        print("       generating MDX...", end=" ", flush=True)
        try:
            mdx = generate_mdx(page_content, url)
            mdx_path = save_mdx(mdx, slug)
            print(f"✓  → {mdx_path.relative_to(Path.cwd()) if mdx_path.is_relative_to(Path.cwd()) else mdx_path}")
        except Exception as e:
            print(f"✗ ({e})")
            mdx = ""

        time.sleep(RATE_LIMIT_DELAY)

        # 3. OpenAPI
        print("       generating OpenAPI...", end=" ", flush=True)
        try:
            spec = generate_openapi(page_content, url, mdx)
            if spec:
                openapi_path = save_openapi(spec, slug)
                print(f"✓  → {openapi_path.relative_to(Path.cwd()) if openapi_path.is_relative_to(Path.cwd()) else openapi_path}")
            else:
                print("✗ (empty spec)")
        except Exception as e:
            print(f"✗ ({e})")

        time.sleep(RATE_LIMIT_DELAY)
        print()

    print("✅  Done!")

if __name__ == "__main__":
    main()
