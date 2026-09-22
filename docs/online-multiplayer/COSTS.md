# Trial costs and operating controls

Checked: 2026-09-22. Target: US$10/month additional spending, 10 concurrent rooms.
These are scenarios, not measured usage or a provider billing cap. No purchase
or deployment has been performed.

## Current price references

Workers Paid has a US$5 monthly base charge. Include it because an existing
subscription is unknown. Free-tier prototypes are possible, but quota failures
must not be confused with a funded trial's budget.
Source: [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

DO Paid includes 1 million requests and 400,000 GB-s monthly; overages are
US$0.15/million requests and US$12.50/million GB-s. Incoming WebSocket messages use
a 20:1 billing conversion. Eligible hibernation avoids duration charges;
non-hibernating objects are billed for allocated 128 MB. Storage is separate.
Billing units can round up, so small overages are not necessarily prorated.
Source: [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/).

Realtime currently includes the first 1,000 GB monthly. TURN beyond the allowance
is US$0.05/GB outgoing to TURN clients, including protocol overhead; STUN is free.
Check actual account entitlements and other Realtime consumption before deployment.
Sources: [Realtime overview](https://developers.cloudflare.com/realtime/),
[TURN billing FAQ](https://developers.cloudflare.com/realtime/turn/faq/#what-is-cloudflare-realtime-turn-pricing-how-exactly-is-it-calculated).

## Illustrative load

Ten occupied rooms for 2 hours/day over 30 days means 600 room-hours. If objects
never hibernate, approximate allocated duration is
`600 * 3600 * 0.128 = 276,480 GB-s`, before other activity. Signaling-only rooms
should permit hibernation, but measure eligibility rather than assuming it.

Assume an effective total 60 directional messages/second per room and 512 metered
bytes/message including overhead/recovery traffic. This gives
`60 * 512 * 3600 / 1e9 = 0.110592 GB/room-hour`, or 66.36 GB for 600 fully relayed
room-hours. Four times the effective bytes/rate gives 265.42 GB. Replace these
assumptions with measured packetization, relay paths and retransmission.

Under included allowances, this scenario could stay near the US$5 subscription
base. That remains conditional on requests, CPU, storage, logs and other account
usage. Static hosting/domain fees remain existing costs; any new provider minimum
or hosting expense must be added. Low estimated cost does not prove good mainland
latency, and other TURN suppliers require separate quotes.

## Proposed controls

- Keep per-frame input and hashes off the DO path; avoid per-frame storage writes.
- Admit at most 10 room leases. A small admission coordinator serializes lease
  allocation without becoming the room/gameplay relay.
- Bound request sizes and creation/join/signaling/credential rates. Clean up idle
  rooms and reconstruct room state safely after hibernation.
- Track usage with headroom for meter delay and outstanding relay credentials.
  Restrict new room creation before the spending target is at risk; preserve
  existing matches where possible.
- Expiring a TURN credential is not proof an existing allocation stops billing.
  Verify revocation/allocation behavior and account for continuing sessions.
- Review actual meters during the trial. Unrelated account usage, abuse and meter
  lag mean this design cannot guarantee an absolute US$10 ceiling.

## Provider gate

Cloudflare TURN is the first managed candidate, not a selected production supplier.
Compare direct WebRTC, forced Cloudflare TURN and an appropriate alternative on
real mainland network pairs. If none meets the connection/performance budget,
report evidence and revisit provider/budget choices rather than silently replacing
the selected transport.
