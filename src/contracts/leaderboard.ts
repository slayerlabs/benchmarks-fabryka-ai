export type Trust = "verified" | "measured" | "reported" | "track";
export type Category = "en" | "pl" | "plen";
export interface BoardRow {
  run_id: string;
  name: string;
  owner: string;
  kind: "track" | "external";
  trust: Trust;
  author: string | null;
  hf_repo: string | null;
  revision: string | null;
  hf_url: string | null;
  n_params: number;
  tokens_seen: number | null;
  checkpoint_sha256: string | null;
  harness: string | null;
  harness_sha: string | null;
  scale_rev: string | null;
  step: number | null;
  label: string;
  evaluated_at: string | null;
  started_at: string;
  finished_at: string | null;
  public_note: string | null;
  categories: Category[];
  en: {
    eff: number | null;
    arc_easy: number | null;
    blimp: number | null;
    wiki_byte_ppl: number | null;
  };
  pl: {
    multiblimp: number | null;
    arc_easy: number | null;
    byte_ppl: number | null;
    eff: number | null;
  };
  /** (eff EN + eff-PL) / 2, server-side; null unless both are present. */
  combined: number | null;
}
export type SortKey =
  | "en_eff"
  | "en_overall"
  | "arc_easy"
  | "blimp"
  | "wiki_byte_ppl"
  | "multiblimp"
  | "pl_arc_easy"
  | "pl_byte_ppl"
  | "pl_eff"
  | "combined"
  | "n_params"
  | "tokens_seen"
  | "date";
export type Direction = "asc" | "desc";
export type SizeKey = "all" | "16" | "32" | "64" | "150" | "350" | "350+";


