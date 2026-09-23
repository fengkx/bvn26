# Short invite code validation

2026-09-23. This is a follow-up to the dated 2026-09-22 server baseline in
[`README.md`](README.md); it preserves that historical output.

The owner receives one short `adjective-animal-xxxxxxxx` code on create and on
the existing sequenced `reinvite` command. Two 32-entry word indexes plus eight
random base32 characters provide 50 bits of entropy. The guest submits the code
in a JSON body with its stable client-generated session token. The Admission DO
indexes by SHA-256 and keeps the raw code only in private retry state. Room
projections contain neither code nor digest. The legacy token-join route remains
available.

Validation covered create-code idempotency; uppercase/whitespace normalization;
same-session join retry; racing different session tokens; sequenced reinvite
retry; no code revival after guest leave; new-code admission; owner closure and
expired-lease revocation; an injected short-code hash collision; and a fixture
which begins with the older `invite_codes` SQLite layout and exercises the
`generation` column migration. That fixture establishes migration behavior for
the modeled old schema; the earlier live database schema was not read directly.

Commands from `services/matchmaking/`:

```sh
npm test
npm run format:check
WRANGLER_SEND_METRICS=false WRANGLER_LOG_PATH=/tmp/bvn-matchmaking-short-code-build.log npm run build
```

Results: **17/17 tests passed**, TypeScript passed, formatting passed, and
Wrangler dry-run build passed without deployment. The production-shaped local
Wrangler listener on `127.0.0.1:8787` also returned create **201** with the
short-code field and owner leave **200** after the schema migration was loaded.
That temporary room was closed. No room ID, code, session token, invitation
token, or request body was retained.

An earlier create attempt against the hot-reloading listener returned
`internal_error`. After the migration and worker bundle refresh, the create/leave
check passed. The exact cause in the pre-migration live SQLite file was not
observed, so this note does not assert that its column layout was the proven
cause. Real two-client browser acceptance is tracked separately from this
service contract.
