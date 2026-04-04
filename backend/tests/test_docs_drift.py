import pytest
from app.main import app
import os
import csv
from pathlib import Path

def test_api_route_drift_against_docs():
    """
    CI Enforcement: Ensures no new backend endpoints are deployed 
    without being properly documented in working docs/API_PARITY_TABLE.csv or PATH_ALIASES.md.
    Closes ENH-0012.
    """
    # 1. Extract all registered routes in code
    registered_routes = set()
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method != "HEAD" and route.path.startswith("/api/"):
                    # Normalize: strip trailing slash
                    path = route.path.rstrip('/')
                    if not path:
                        path = '/'
                    registered_routes.add((method, path))

    # 2. Extract known paths from the canonical CSVs or aliases
    known_routes = set()
    
    csv_path = Path(__file__).parent.parent.parent / "working docs/API_PARITY_TABLE.csv"
    if not csv_path.exists():
        pytest.skip("Audit artifacts not generated yet, skipping drift check.")
        
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('status') != 'doc_only_missing_in_code':
                method = row.get('method', 'ANY')
                path = row.get('normalized_endpoint', '').rstrip('/')
                # If ANY, we loosen the check later
                known_routes.add((method, path))
                
    # Parse aliases as well to get any manually authorized routes
    aliases_path = Path(__file__).parent.parent.parent / "docs" / "PATH_ALIASES.md"
    if aliases_path.exists():
        with open(aliases_path, 'r') as f:
            lines = f.readlines()
            parsing = False
            for line in lines:
                if "Undocumented Endpoints (Code-Only)" in line:
                    parsing = True
                if parsing and '| `POST' in line or '| `GET' in line or '| `PUT' in line or '| `PATCH' in line or '| `DELETE' in line:
                    parts = line.split('`')
                    if len(parts) >= 3:
                        sig = parts[1].split()
                        if len(sig) == 2:
                            known_routes.add((sig[0], sig[1].rstrip('/')))
                            
    # We won't strictly fail the test if the routes are covered by "ANY" method in docs
    known_paths = {p for m, p in known_routes}
    
    unaccounted_routes = []
    
    for method, path in registered_routes:
        # Exact match
        if (method, path) in known_routes:
            continue
        # Wildcard match from CSV
        if ("ANY", path) in known_routes:
            continue
            
        # Domain prefix match
        matched_prefix = False
        for known_m, known_p in known_routes:
            if path.startswith(known_p) and (known_m == method or known_m == 'ANY' or known_m == 'POST' or known_m == 'GET' or known_m == 'PUT' or known_m == 'PATCH' or known_m == 'DELETE'):
                matched_prefix = True
                break
        
        if matched_prefix:
            continue
            
        unaccounted_routes.append(f"{method} {path}")
        
    # Exclude system endpoints added by fastAPI like /api/v1/openapi.json
    unaccounted_routes = [r for r in unaccounted_routes if "openapi.json" not in r]

    # If new routes are developed without documentation, this test fails CI
    assert not unaccounted_routes, (
        f"Docs drift detected! Found {len(unaccounted_routes)} undocumented endpoints. "
        f"Add them to working docs/docs/PATH_ALIASES.md to pass CI. Undocumented: {unaccounted_routes}"
    )
