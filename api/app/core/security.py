# No authentication is enforced yet — the API is only reachable from the
# local dev frontend at this stage. This module exists so that adding
# API-key or JWT auth later doesn't require restructuring the routes:
# a route would simply add `Depends(require_api_key)` from here.
#
# Left intentionally empty of real logic until auth is actually needed
# (see project constraint: don't build features that aren't required yet).
