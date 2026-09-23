const adjectives = [
  "amber",
  "brisk",
  "calm",
  "clever",
  "cozy",
  "crisp",
  "dawn",
  "eager",
  "fair",
  "fresh",
  "gentle",
  "gold",
  "happy",
  "kind",
  "lucky",
  "mellow",
  "mint",
  "noble",
  "peach",
  "quiet",
  "rapid",
  "ready",
  "sunny",
  "sweet",
  "swift",
  "tidy",
  "warm",
  "wise",
  "bright",
  "blue",
  "coral",
  "silver",
] as const;

const animals = [
  "badger",
  "bear",
  "bee",
  "bison",
  "cat",
  "cobra",
  "crane",
  "deer",
  "dolphin",
  "dragon",
  "eagle",
  "elk",
  "falcon",
  "fox",
  "frog",
  "gecko",
  "goose",
  "heron",
  "horse",
  "koala",
  "lemur",
  "lion",
  "lizard",
  "lynx",
  "otter",
  "panda",
  "rabbit",
  "raven",
  "seal",
  "tiger",
  "yak",
  "zebra",
] as const;

const alphabet = "abcdefghijklmnopqrstuvwxyz234567";

export function normalizeInviteCode(value: string): string {
  return value.trim().toLowerCase();
}

export function validInviteCode(value: string): boolean {
  const [adjective, animal, suffix, ...rest] =
    normalizeInviteCode(value).split("-");
  return (
    rest.length === 0 &&
    adjectives.includes(adjective as (typeof adjectives)[number]) &&
    animals.includes(animal as (typeof animals)[number]) &&
    /^[a-z2-7]{8}$/.test(suffix ?? "")
  );
}

export function generateInviteCode(): string {
  const random = crypto.getRandomValues(new Uint8Array(10));
  const adjective = adjectives[random[0] & 31];
  const animal = animals[random[1] & 31];
  let suffix = "";
  for (let index = 2; index < 10; index++)
    suffix += alphabet[random[index] & 31];
  return `${adjective}-${animal}-${suffix}`;
}
