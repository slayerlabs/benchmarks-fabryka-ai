import type { BoardRow } from "../contracts/leaderboard";
/** Read-only published response. Categories, eff, combined and granted trust come from the source. */
export interface LeaderboardResponse { models: BoardRow[] }
export interface LeaderboardSource { load(): Promise<LeaderboardResponse> }

