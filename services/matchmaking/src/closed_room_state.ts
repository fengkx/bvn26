import { member, type State } from "./state";

export function closedRoomState(state: State): State {
  return {
    schema: 1,
    id: state.id,
    creationHash: state.creationHash,
    inviteHash: "",
    shortInviteHash: null,
    compatibility: state.compatibility,
    revision: state.revision,
    setupRevision: state.setupRevision,
    members: [member("", ""), null],
    stage: state.stage,
    rules: state.rules,
    phase: "closed",
    match: null,
    lastResult: null,
    negotiation: null,
    lastActivity: 0,
    leaseUntil: 0,
    createdAt: state.createdAt,
  };
}
