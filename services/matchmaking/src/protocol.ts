import { z } from "zod";

export const VERSION = 1;
export const MAX_BYTES = 16_384;
export const IDLE_MS = 30 * 60_000;
export const PREPARE_MS = 30_000;
export const TICKET_MS = 30_000;
export const token = z.string().regex(/^[A-Za-z0-9_-]{43}$/);
export const digest = z.string().regex(/^[a-f0-9]{64}$/);
const id = z.string().min(1).max(80);
const revision = z.number().int().nonnegative();
export const compatibility = z.strictObject({
  protocol: z.literal(VERSION),
  build: digest,
  content: digest,
});
const nickname = z
  .string()
  .trim()
  .min(1)
  .max(32)
  .regex(/^[^\p{Cc}\p{Cf}<>]*$/u);
export const create = z
  .strictObject({
    createToken: token,
    sessionToken: token,
    inviteToken: token,
    nickname,
    compatibility,
  })
  .refine(
    (value) =>
      new Set([value.createToken, value.sessionToken, value.inviteToken])
        .size === 3,
  );
export const join = z
  .strictObject({
    sessionToken: token,
    inviteToken: token,
    nickname,
    compatibility,
  })
  .refine((value) => value.sessionToken !== value.inviteToken);
export const joinByCode = z.strictObject({
  code: z.string().trim().min(1).max(64),
  sessionToken: token,
  nickname,
  compatibility,
});
export const profile = z.strictObject({
  id,
  inputDelay: z.number().int().min(0).max(8),
  predictionWindow: z.number().int().min(0).max(15),
});
export const choice = z.strictObject({ fighter: id, helper: id });
export const rules = z.strictObject({
  time: z.union([z.literal(30), z.literal(60), z.literal(90), z.literal(100)]),
  life: z.union([
    z.literal(1),
    z.literal(2),
    z.literal(3),
    z.literal(4),
    z.literal(5),
  ]),
});
const epoch = z.string().uuid();
export const operation = z.discriminatedUnion("type", [
  z.strictObject({ type: z.literal("select"), revision, choice }),
  z.strictObject({ type: z.literal("configure"), revision, stage: id, rules }),
  z.strictObject({
    type: z.literal("ready"),
    revision,
    ready: z.boolean(),
    profile,
  }),
  z.strictObject({ type: z.literal("prepare"), revision }),
  z.strictObject({ type: z.literal("loaded"), epoch, initialHash: digest }),
  z.strictObject({ type: z.literal("start_ack"), epoch }),
  z.strictObject({
    type: z.literal("result"),
    epoch,
    frame: revision,
    hash: digest,
    winner: z.union([z.literal(0), z.literal(1), z.null()]),
  }),
  z.strictObject({ type: z.literal("abort"), epoch }),
  z.strictObject({ type: z.literal("negotiate"), epoch: epoch.nullable() }),
  z.strictObject({ type: z.literal("reinvite"), inviteToken: token }),
  z.strictObject({ type: z.literal("leave") }),
  z.strictObject({ type: z.literal("keepalive") }),
]);
export const command = z.strictObject({
  version: z.literal(VERSION),
  seq: z.number().int().positive().max(Number.MAX_SAFE_INTEGER),
  operation,
});
export const signal = z.strictObject({
  version: z.literal(VERSION),
  type: z.literal("signal"),
  seq: revision,
  epoch: epoch.nullable(),
  negotiationId: z.string().uuid(),
  kind: z.enum(["offer", "answer", "candidate"]),
  payload: z.string().min(1).max(12_000),
});
export type Compatibility = z.infer<typeof compatibility>;
export type Profile = z.infer<typeof profile>;
export type Choice = z.infer<typeof choice>;
export type Rules = z.infer<typeof rules>;
export type Command = z.infer<typeof command>;
export type Create = z.infer<typeof create>;
export type Join = z.infer<typeof join>;
export class Fault extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(code);
  }
}
export function requireThat(
  value: unknown,
  code: string,
  status = 409,
): asserts value {
  if (!value) throw new Fault(status, code);
}
export function parse<T>(schema: z.ZodType<T>, value: unknown): T {
  const result = schema.safeParse(value);
  if (!result.success) throw new Fault(400, "invalid_message");
  return result.data;
}
export function json(value: unknown, status = 200): Response {
  return Response.json(value, {
    status,
    headers: { "Cache-Control": "no-store" },
  });
}
export function failure(error: unknown): Response {
  return error instanceof Fault
    ? json({ error: error.code }, error.status)
    : json({ error: "internal_error" }, 500);
}
export async function body(request: Request): Promise<unknown> {
  requireThat(
    request.headers.get("Content-Type")?.split(";")[0] === "application/json",
    "json_required",
    415,
  );
  const reader = request.body?.getReader();
  requireThat(reader, "body_required", 400);
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > MAX_BYTES) {
      await reader.cancel();
      throw new Fault(413, "message_too_large");
    }
    chunks.push(part.value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    throw new Fault(400, "invalid_json");
  }
}
export async function hash(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
export function secret(): string {
  return btoa(
    String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32))),
  )
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}
