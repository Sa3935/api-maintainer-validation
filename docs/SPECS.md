# Spec provenance

Both specs are the real published Stripe OpenAPI specs, downloaded
unmodified from the public `stripe/openapi` GitHub repo
(https://github.com/stripe/openapi). No spec file in this repo was
hand-written or edited.

| File | Stripe API version | Source commit | Commit date |
|---|---|---|---|
| `spec3-2026-03-25.dahlia.yaml` | `2026-03-25.dahlia` | `a54c3888eb6f` | 2026-03-23 |
| `spec3-2026-09-30.endive.yaml` | `2026-09-30.endive` | `bcfd59f49dca` (master at fetch time) | 2026-09-29 |

Notes:
- The 2026-03-25 spec was fetched via the commit dated 2026-03-23;
  its `info.version` field reads `2026-03-25.dahlia`, which is the
  version the app code in `app/` was written against.
- The endive spec was fetched from master; its `info.version` reads
  `2026-09-30.endive`. (A later endive monthly release,
  2026-10-28.endive, exists; it is additive-only, so it does not change
  any of the three breaks tested here.)
- The dahlia spec published 2026-07-29 (`af5309cae53e`) was also checked
  during research; it was not needed as a baseline because the app pins
  2026-03-25.dahlia.

Verification you can repeat:
```bash
python3 -c "
import yaml
for f in ['specs/spec3-2026-03-25.dahlia.yaml',
          'specs/spec3-2026-09-30.endive.yaml']:
    spec = yaml.safe_load(open(f))
    print(f, '->', spec['info']['version'])
"
```
