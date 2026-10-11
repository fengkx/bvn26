import {
  type Choice,
  type Command,
  type Compatibility,
  type Profile,
  type Rules,
  NEGOTIATION_MAX_LIFETIME_MS,
  NEGOTIATION_TTL_MS,
  PREPARE_MS,
  requireThat,
} from "./protocol";
import catalog from "./catalog.json";

export interface Member {
  credential: string;
  nickname: string;
  choice: Choice | null;
  ready: boolean;
  profile: Profile | null;
  seq: number;
  lastCommand: string | null;
  lastReply: unknown;
  connection: string | null;
}
interface Result {
  frame: number;
  hash: string;
  winner: 0 | 1 | null;
}
export interface Match {
  epoch: string;
  seed: number;
  clockBaseline: number;
  profile: Profile;
  deadline: number;
  loaded: [string | null, string | null];
  acknowledged: [boolean, boolean];
  results: [Result | null, Result | null];
}
export interface State {
  schema: 1;
  id: string;
  creationHash: string;
  inviteHash: string;
  shortInviteHash?: string | null;
  compatibility: Compatibility;
  revision: number;
  setupRevision: number;
  members: [Member, Member | null];
  stage: string;
  rules: Rules;
  networkProfile?: Profile;
  phase: "lobby" | "preparing" | "active" | "closed";
  match: Match | null;
  lastResult: { epoch: string; winner: 0 | 1 | null; reason: string } | null;
  negotiation: {
    id: string;
    epoch: string | null;
    created: number;
    expires: number;
  } | null;
  lastActivity: number;
  leaseUntil: number;
  createdAt?: number;
}
export const DEFAULT_NETWORK_PROFILE: Profile = {
  id: "chrome-exp-d2-p6",
  inputDelay: 2,
  predictionWindow: 6,
};
export function networkProfile(state: State): Profile {
  return state.networkProfile ?? DEFAULT_NETWORK_PROFILE;
}
function sameProfile(
  left: Profile | null | undefined,
  right: Profile,
): boolean {
  return (
    !!left &&
    left.id === right.id &&
    left.inputDelay === right.inputDelay &&
    left.predictionWindow === right.predictionWindow
  );
}
export function member(credential: string, nickname: string): Member {
  return {
    credential,
    nickname,
    choice: null,
    ready: false,
    profile: null,
    seq: 0,
    lastCommand: null,
    lastReply: null,
    connection: null,
  };
}
export function projection(
  state: State,
  signaling: readonly [boolean, boolean] = [false, false],
): unknown {
  const {
    creationHash: _creation,
    inviteHash: _invite,
    shortInviteHash: _shortInvite,
    networkProfile: _networkProfile,
    createdAt: _createdAt,
    members,
    ...publicState
  } = state;
  return {
    ...publicState,
    networkProfile: networkProfile(state),
    members: members.map(
      (seat, index) =>
        seat && {
          nickname: seat.nickname,
          choice: seat.choice,
          ready: seat.ready,
          profile: seat.profile,
          seq: seat.seq,
          signaling: signaling[index] === true,
        },
    ),
  };
}
export function invalidate(state: State): void {
  state.setupRevision++;
  for (const seat of state.members)
    if (seat) {
      seat.ready = false;
      seat.profile = null;
    }
  state.negotiation = null;
}
export function finish(
  state: State,
  reason: string,
  winner: 0 | 1 | null = null,
): void {
  if (state.match)
    state.lastResult = { epoch: state.match.epoch, reason, winner };
  state.phase = "lobby";
  state.match = null;
  invalidate(state);
}
export function apply(
  state: State,
  slot: 0 | 1,
  command: Command,
  now: number,
  inviteHash?: string,
  shortInviteHash?: string,
): void {
  const op = command.operation;
  const seat = state.members[slot]!;
  if ("revision" in op) {
    requireThat(state.phase === "lobby", "not_in_lobby");
    requireThat(op.revision === state.setupRevision, "stale_revision");
  }
  if ("epoch" in op && op.type !== "negotiate")
    requireThat(state.match?.epoch === op.epoch, "stale_epoch");
  switch (op.type) {
    case "select":
      requireThat(
        catalog.fighters.includes(op.choice.fighter) &&
          catalog.helpers.includes(op.choice.helper),
        "unsupported_content",
        400,
      );
      seat.choice = op.choice;
      invalidate(state);
      break;
    case "configure":
      requireThat(slot === 0, "owner_required", 403);
      requireThat(
        catalog.stages.includes(op.stage),
        "unsupported_content",
        400,
      );
      state.stage = op.stage;
      state.rules = op.rules;
      invalidate(state);
      break;
    case "configure_network":
      requireThat(slot === 0, "owner_required", 403);
      {
        const current = networkProfile(state);
        state.networkProfile = { ...op.profile };
        if (!sameProfile(current, op.profile)) invalidate(state);
      }
      break;
    case "ready":
      requireThat(seat.choice && state.members[1], "incomplete_setup");
      if (op.ready)
        requireThat(
          sameProfile(op.profile, networkProfile(state)),
          "network_profile_mismatch",
        );
      seat.ready = op.ready;
      seat.profile = op.ready ? { ...networkProfile(state) } : null;
      break;
    case "prepare": {
      requireThat(slot === 0, "owner_required", 403);
      const guest = state.members[1];
      const authority = networkProfile(state);
      requireThat(
        seat.ready &&
          guest?.ready &&
          sameProfile(seat.profile, authority) &&
          sameProfile(guest.profile, authority),
        "not_ready",
      );
      state.match = {
        epoch: crypto.randomUUID(),
        seed: crypto.getRandomValues(new Uint32Array(1))[0],
        clockBaseline: 0,
        profile: { ...authority },
        deadline: now + PREPARE_MS,
        loaded: [null, null],
        acknowledged: [false, false],
        results: [null, null],
      };
      state.phase = "preparing";
      state.negotiation = null;
      break;
    }
    case "loaded": {
      requireThat(state.phase === "preparing", "not_preparing");
      const match = state.match!;
      requireThat(
        !match.loaded[slot] || match.loaded[slot] === op.initialHash,
        "conflicting_initial_state",
      );
      match.loaded[slot] = op.initialHash;
      if (
        match.loaded[0] &&
        match.loaded[1] &&
        match.loaded[0] !== match.loaded[1]
      )
        finish(state, "initial_state_mismatch");
      break;
    }
    case "start_ack": {
      const match = state.match!;
      requireThat(
        state.phase === "preparing" &&
          match.loaded[0] &&
          match.loaded[0] === match.loaded[1],
        "load_barrier_pending",
      );
      match.acknowledged[slot] = true;
      if (match.acknowledged.every(Boolean)) state.phase = "active";
      break;
    }
    case "result": {
      requireThat(state.phase === "active", "not_active");
      const match = state.match!;
      const result = { frame: op.frame, hash: op.hash, winner: op.winner };
      requireThat(
        !match.results[slot] ||
          JSON.stringify(match.results[slot]) === JSON.stringify(result),
        "conflicting_result",
      );
      match.results[slot] = result;
      if (match.results[0] && match.results[1]) {
        const agreed =
          JSON.stringify(match.results[0]) === JSON.stringify(match.results[1]);
        finish(
          state,
          agreed ? "agreed" : "result_mismatch",
          agreed ? op.winner : null,
        );
      }
      break;
    }
    case "abort":
      finish(state, "aborted");
      break;
    case "negotiate":
      requireThat(
        slot === 0 && state.members[1],
        "owner_and_peer_required",
        403,
      );
      requireThat(op.epoch === (state.match?.epoch ?? null), "stale_epoch");
      {
        const existing = state.negotiation;
        // A new PeerConnection needs a new id, including for legacy clients.
        // Only an explicit resume may extend an existing handshake.
        if (op.resumeNegotiationId !== undefined)
          requireThat(
            existing?.id === op.resumeNegotiationId,
            "stale_negotiation",
          );
        // Rows written before `created` existed count their remaining TTL as age.
        const created =
          existing?.created ??
          (existing ? existing.expires - NEGOTIATION_TTL_MS : now);
        const lifetimeEnd = created + NEGOTIATION_MAX_LIFETIME_MS;
        if (
          existing &&
          op.resumeNegotiationId === existing.id &&
          existing.epoch === op.epoch &&
          existing.expires > now &&
          now < lifetimeEnd
        ) {
          existing.created = created;
          existing.expires = Math.min(now + NEGOTIATION_TTL_MS, lifetimeEnd);
          break;
        }
      }
      state.negotiation = {
        id: crypto.randomUUID(),
        epoch: op.epoch,
        created: now,
        expires: now + NEGOTIATION_TTL_MS,
      };
      break;
    case "reinvite":
      requireThat(slot === 0, "owner_required", 403);
      requireThat(state.phase === "lobby", "not_in_lobby");
      state.inviteHash = inviteHash!;
      state.shortInviteHash = shortInviteHash!;
      break;
    case "leave":
      finish(state, "participant_left");
      state.shortInviteHash = null;
      if (slot === 0) state.phase = "closed";
      else {
        state.members[1] = null;
        state.shortInviteHash = null;
      }
      break;
    case "keepalive":
      break;
  }
  state.revision++;
  state.lastActivity = now;
}
