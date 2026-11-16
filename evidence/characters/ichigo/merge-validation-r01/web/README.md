# Local Web export validation

The standard Web build passed strict import/export log scans and manifest checks.
The retained sidecar binds the tested PCK hash and frozen snapshot identity.
The snapshot accurately reports dirty paths (generated UID/import metadata,
local template binding and, for the final roster, integration changes). It is
not represented as a clean-commit build. Subsequent evidence-only commits do
not alter the runtime tested here.

The packed roster check loaded the exported PCK and required replacement forms,
and rejected a deliberately missing form profile. Chromium loaded this exact
local dist/web export, reached M0_BOOT_OK and rendered a visible canvas without
script errors. This verifies startup, not exhaustive browser gameplay parity.
The generated Web bundle and browser profile remain outside tracked sources.
