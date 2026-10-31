import { fixtureModels } from "../fixtures/models.ts";
import type { LeaderboardSource } from "./source";
export const fixtureSource: LeaderboardSource = {
  async load() { return { models: structuredClone(fixtureModels) }; },
};
