#!/usr/bin/env python3
"""
Export the OpenAPI spec from the running FastAPI app.

Usage:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --output path/to/openapi.json

The spec is written to openapi.json in the repo root by default.
This script is called by the publish-clients.yml workflow on every merge to main.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add repo root to path so src can be imported
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Set required env vars for app import (values don't matter for spec export)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://placeholder/placeholder")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")
os.environ.setdefault("SUPABASE_JWT_SECRET", "placeholder-secret-32-chars-minimum-x")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI spec")
    parser.add_argument(
        "--output",
        default=str(repo_root / "openapi.json"),
        help="Output path for openapi.json (default: repo root)",
    )
    args = parser.parse_args()

    from src.main import app

    spec = app.openapi()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)

    print(f"✓ OpenAPI spec exported to {output_path}")
    print(f"  Title   : {spec.get('info', {}).get('title')}")
    print(f"  Version : {spec.get('info', {}).get('version')}")
    print(f"  Paths   : {len(spec.get('paths', {}))}")


if __name__ == "__main__":
    main()
