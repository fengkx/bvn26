import assert from "node:assert/strict";
import test from "node:test";
import {
  localPermissionOrigin,
  rtcDiagnostics,
} from "../authority_browser_diagnostics.mjs";

test("permission override is limited to a local HTTP test origin", () => {
  assert.equal(
    localPermissionOrigin("http://127.0.0.1:8078/index.html"),
    "http://127.0.0.1:8078",
  );
  assert.equal(
    localPermissionOrigin("http://[::1]:8078/"),
    "http://[::1]:8078",
  );
  for (const url of [
    "https://example.com/",
    "http://192.168.1.1/",
    "http://localhost.example.com/",
    "file:///game.html",
  ])
    assert.throws(() => localPermissionOrigin(url));
});

test("serialized browser diagnostics prove a selected pair without leaking addresses or credentials", async () => {
  const rows = [
    {
      id: "local",
      type: "local-candidate",
      address: "127.0.0.1",
      candidateType: "host",
      protocol: "udp",
      usernameFragment: "do-not-export",
    },
    {
      id: "remote",
      type: "remote-candidate",
      address: "192.168.1.45",
      candidateType: "host",
      protocol: "udp",
    },
    {
      id: "pair",
      type: "candidate-pair",
      localCandidateId: "local",
      remoteCandidateId: "remote",
      state: "succeeded",
      nominated: true,
      bytesSent: 42,
      bytesReceived: 21,
    },
    { id: "transport", type: "transport", selectedCandidatePairId: "pair" },
  ];
  globalThis.authorityRtc = [
    {
      connectionState: "connected",
      iceConnectionState: "connected",
      signalingState: "stable",
      authorityCalls: [],
      authorityChannels: [{ label: "state", readyState: "open" }],
      getStats: async () => new Map(rows.map((row) => [row.id, row])),
    },
  ];
  try {
    const result = await (0, eval)(`(${rtcDiagnostics.toString()})()`);
    assert.equal(result[0].selectedPair.localAddressClass, "loopback");
    assert.equal(result[0].selectedPair.remoteAddressClass, "private");
    assert.equal(result[0].selectedPair.bytesSent, 42);
    assert.equal(result[0].channels[0].state, "open");
    for (const secret of ["127.0.0.1", "192.168.1.45", "do-not-export"])
      assert.ok(!JSON.stringify(result).includes(secret));
  } finally {
    delete globalThis.authorityRtc;
  }
});
