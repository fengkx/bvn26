// This function is serialized into the dedicated test page. Keep it self-contained.
export async function rtcDiagnostics() {
  function addressClass(address) {
    if (!address) return "hidden";
    if (address === "::1" || address.startsWith("127.")) return "loopback";
    if (address.endsWith(".local")) return "mdns";
    if (/^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)/.test(address))
      return "private";
    if (/^198\.(18|19)\./.test(address)) return "benchmark-range";
    return "other";
  }
  return Promise.all(
    (globalThis.authorityRtc ?? []).map(async (peer) => {
      const stats = await peer.getStats();
      const candidates = [...stats.values()].filter((row) =>
        row.type.endsWith("-candidate"),
      );
      const transport = [...stats.values()].find(
        (row) => row.type === "transport" && row.selectedCandidatePairId,
      );
      const selected =
        transport && stats.get(transport.selectedCandidatePairId);
      const local = selected && stats.get(selected.localCandidateId);
      const remote = selected && stats.get(selected.remoteCandidateId);
      return {
        connection: peer.connectionState,
        ice: peer.iceConnectionState,
        signaling: peer.signalingState,
        calls: peer.authorityCalls,
        channels: peer.authorityChannels?.map((channel) => ({
          label: channel.label,
          state: channel.readyState,
        })),
        candidates: candidates.map((row) => ({
          side: row.type,
          type: row.candidateType,
          protocol: row.protocol,
          addressClass: addressClass(row.address),
        })),
        selectedPair: selected
          ? {
              state: selected.state,
              nominated: selected.nominated,
              bytesSent: selected.bytesSent,
              bytesReceived: selected.bytesReceived,
              requestsSent: selected.requestsSent,
              responsesReceived: selected.responsesReceived,
              localType: local?.candidateType,
              remoteType: remote?.candidateType,
              localAddressClass: addressClass(local?.address),
              remoteAddressClass: addressClass(remote?.address),
              protocol: local?.protocol,
            }
          : null,
      };
    }),
  );
}

export function localPermissionOrigin(url) {
  const parsed = new URL(url);
  if (
    parsed.protocol !== "http:" ||
    !["127.0.0.1", "localhost", "[::1]"].includes(parsed.hostname)
  )
    throw new Error(
      "Local ICE permission override requires a loopback HTTP test origin",
    );
  return parsed.origin;
}
