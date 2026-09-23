import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("server content IDs match the enabled menu catalog", async () => {
  const read = async (path) =>
    JSON.parse(await readFile(new URL(path, import.meta.url), "utf8"));
  const catalog = await read("../src/catalog.json");
  const available = await read(
    "../../../godot/generated/main/character_selection/available.json",
  );
  const stages = await read(
    "../../../godot/generated/main/map_selection/presentation.json",
  );
  assert.deepEqual(catalog.fighters, Object.values(available.fighters));
  assert.deepEqual(catalog.helpers, Object.values(available.helpers));
  assert.deepEqual(
    catalog.stages,
    stages.cards.map((card) => card.id),
  );
});
