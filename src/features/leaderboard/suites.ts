import type { Category, Direction, SortKey } from "../../contracts/leaderboard.ts";

export interface Metric {
  key: SortKey;
  label: string;
  unit: "score" | "%" | "byte-PPL";
  direction: Direction;
  note?: string;
  digits: number;
  dagger?: boolean;
}
export interface BenchmarkSuite {
  id: string;
  label: string;
  version: string;
  category: Category;
  primary: Metric;
  secondary: Metric[];
  documentation: string;
  summary: string;
}
const score = (key: SortKey, label: string, dagger = false): Metric =>
  ({ key, label, unit: "score", direction: "desc", digits: 2, dagger });
const accuracy = (key: SortKey, label: string, dagger = false): Metric =>
  ({ key, label, unit: "%", direction: "desc", digits: 2, dagger });
const perplexity = (key: SortKey, label: string, dagger = false): Metric =>
  ({ key, label, unit: "byte-PPL", direction: "asc", digits: 4, dagger, note: "lower is better" });
export const benchmarkSuites: readonly BenchmarkSuite[] = [
  { id: "en", label: "EN", version: "legacy-display-v1", category: "en",
    primary: { ...score("en_eff", "eff"), note: "per scale revision" },
    secondary: [{ ...score("en_overall", "Overall"), note: "Glint, no size bonus" }, accuracy("arc_easy", "ARC-Easy"), accuracy("blimp", "BLiMP"), perplexity("wiki_byte_ppl", "Wiki byte-PPL")],
    documentation: "/methodology#english", summary: "English · ranked by eff by default. Higher is better." },
  { id: "pl", label: "PL", version: "legacy-display-v1", category: "pl",
    primary: score("pl_eff", "eff-PL", true),
    secondary: [{ ...accuracy("multiblimp", "MultiBLiMP-pl accuracy", true), note: "length baseline ≈ 60 %" }, accuracy("pl_arc_easy", "ARC-Easy-PL accuracy", true), perplexity("pl_byte_ppl", "byte-PPL PL", true)],
    documentation: "/methodology#polish", summary: "Polish · missing eff-PL stays unranked; no scores are imputed." },
  { id: "plen", label: "PL+EN", version: "legacy-display-v1", category: "plen",
    primary: score("combined", "PL+EN", true),
    secondary: [score("en_eff", "eff EN"), score("pl_eff", "eff-PL", true)],
    documentation: "/methodology#combined", summary: "Bilingual · combined score for the same model checkpoint." },
];
