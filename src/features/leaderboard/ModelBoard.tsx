import { useState } from "react";
import { PageTop } from "../../components/PageTop";
import { fixtureSource } from "../../data/fixture-source";
import type { LeaderboardSource } from "../../data/source";
import { useEffect } from "react";
import { compact, format } from "./format";
import {
  NATURAL_DIRECTION,
  SIZE_BUCKETS,
  TRUST_LABELS,
  checkpointDetails,
  filterRows,
  hfLink,
  measuredByUs,
  rankKey,
  rankRows,
  sizeBucket,
  sortRows,
  sortValue,
} from "./model-board-data";
import type {
  BoardRow,
  Category,
  Direction,
  RankAxis,
  SizeKey,
  SortKey,
} from "./model-board-data";
import "./leaderboard.css";

const CATEGORY_LABELS: Record<Category, string> = {
  en: "EN",
  pl: "PL",
  plen: "PL+EN",
};
// dagger: a value we measured for an external model with our protocol.
type Column = {
  key: SortKey;
  label: string;
  note?: string;
  digits?: number;
  dagger?: boolean;
};
const SCORE_COLUMNS: Record<Category, Column[]> = {
  en: [
    { key: "en_eff", label: "eff", note: "per scale revision", digits: 2 },
    {
      key: "en_overall",
      label: "Overall",
      note: "Glint, no size bonus",
      digits: 2,
    },
    { key: "arc_easy", label: "ARC-Easy", digits: 2 },
    { key: "blimp", label: "BLiMP", digits: 2 },
    {
      key: "wiki_byte_ppl",
      label: "Wiki byte-PPL",
      note: "lower is better",
      digits: 4,
    },
  ],
  pl: [
    {
      key: "multiblimp",
      label: "MultiBLiMP-pl accuracy",
      note: "length baseline ≈ 60 %",
      digits: 2,
      dagger: true,
    },
    {
      key: "pl_arc_easy",
      label: "ARC-Easy-PL accuracy",
      digits: 2,
      dagger: true,
    },
    {
      key: "pl_byte_ppl",
      label: "byte-PPL PL",
      note: "lower is better",
      digits: 4,
      dagger: true,
    },
    { key: "pl_eff", label: "eff-PL", digits: 2, dagger: true },
  ],
  plen: [
    { key: "combined", label: "PL+EN", digits: 2, dagger: true },
    { key: "en_eff", label: "eff EN", digits: 2 },
    { key: "pl_eff", label: "eff-PL", digits: 2, dagger: true },
  ],
};
const CATEGORY_NOTES: Record<Category, string> = {
  en: "Ranked by eff: the Glint Tiny-ML efficiency score (0–100) for owner-marked rows, the track's Tiny-ML efficiency for rows measured by track. Each row shows its scale revision. The size bonus stops at 150M parameters (Glint formula), so larger models get no bonus.",
  pl: "Ranked by eff-PL = (G + K + WS) / 3 × the same size multiplier as EN; our protocol, not official. G = MultiBLiMP-pl accuracy (length baseline ≈ 60 %: always picking the shorter sentence scores about 60 %), K = ARC-Easy-PL accuracy, WS = score from byte-PPL on frozen Polish W (text public since 2026-10-25; check training-data overlap). Rows without eff-PL are listed below, unranked, by MultiBLiMP-pl.",
  plen: "Average of eff EN and eff-PL; favours bilingual models. Shown only for models with both.",
};
const EN_OVERALL_NOTE =
  "Ranked by Overall = (BLiMP + ARC-Easy + WikiText score) / 3, the Glint Tiny-ML overall score without the size bonus, computed in the browser from the row's published values.";
/** A cell carries the dagger when it is our measurement of an external model. */
const daggered = (row: BoardRow, column: Column) =>
  !!column.dagger && measuredByUs(row) && sortValue(row, column.key) !== null;

function BoardTable({
  rows,
  category,
  rankedKey,
  columns,
  ranks,
  sort,
  onSort,
}: {
  rows: BoardRow[];
  category: Category;
  rankedKey: SortKey;
  columns: Column[];
  ranks: Map<string, number>;
  sort: { key: SortKey; direction: Direction };
  onSort: (key: SortKey) => void;
}) {
  const header = (column: Column) => (
    <th
      scope="col"
      key={column.key}
      aria-sort={
        sort.key === column.key
          ? sort.direction === "asc"
            ? "ascending"
            : "descending"
          : "none"
      }
    >
      <button className="mb-sort" onClick={() => onSort(column.key)}>
        {column.label}
        <span aria-hidden="true">
          {sort.key === column.key
            ? sort.direction === "asc"
              ? " ▲"
              : " ▼"
            : ""}
        </span>
        {column.note && <small>{column.note}</small>}
      </button>
    </th>
  );
  return (
    <div
      className="lb-table-scroll"
      tabIndex={0}
      role="region"
      aria-label={`${CATEGORY_LABELS[category]} model results`}
    >
      <table className="lb-table mb-table">
        <thead>
          <tr>
            <th scope="col">Rank</th>
            <th scope="col">Model</th>
            <th scope="col">Author</th>
            {columns.map(header)}
            {header({ key: "n_params", label: "Params" })}
            {header({ key: "tokens_seen", label: "Tokens" })}
            <th scope="col">Trust</th>
            {header({ key: "date", label: "Date" })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const hf = hfLink(row);
            return (
              <tr key={row.run_id}>
                <td className="lb-number mb-rank">
                  {ranks.get(row.run_id) ?? "—"}
                </td>
                <td className="lb-run-name">
                  {hf ? (
                    <a href={hf} target="_blank" rel="noopener noreferrer">
                      {row.name} ↗
                    </a>
                  ) : (
                    <strong>{row.name}</strong>
                  )}
                  <span className="mb-model-meta">
                    {row.kind === "external"
                      ? `HF checkpoint · ${row.revision?.slice(0, 8) ?? "revision unavailable"}`
                      : `Track run · ${row.owner}`}
                  </span>
                  <details className="mb-model-details">
                    <summary>Details</summary>
                    <div className="mb-model-detail-content">
                      {row.kind === "external" && row.hf_repo && (
                        <small>
                          Hugging Face: {row.hf_repo}
                          {row.revision ? `@${row.revision}` : ""} · logged by {row.owner}
                        </small>
                      )}
                      <small>
                        {checkpointDetails(row)}
                        {row.scale_rev ? " · " : ""}
                        {row.scale_rev && (
                          <abbr title="eff depends on the min/max ranges of its scale; compare eff only between rows with the same scale revision.">
                            scale {row.scale_rev}
                          </abbr>
                        )}
                        {row.harness || row.harness_sha
                          ? ` · harness ${[row.harness, row.harness_sha?.slice(0, 8)].filter(Boolean).join(" @ ")}`
                          : ""}
                      </small>
                      {row.public_note && (
                        <small className="mb-note">{row.public_note}</small>
                      )}
                    </div>
                  </details>
                </td>
                <td>{row.author ?? row.owner}</td>
                {columns.map((column) => {
                  const text =
                    format(sortValue(row, column.key), column.digits) +
                    (daggered(row, column) ? "†" : "");
                  return (
                    <td className="lb-number" key={column.key}>
                      {column.key === rankedKey ? (
                        <strong>{text}</strong>
                      ) : (
                        text
                      )}
                    </td>
                  );
                })}
                <td className="lb-number">{compact(row.n_params)}</td>
                <td className="lb-number">{compact(row.tokens_seen)}</td>
                <td>
                  <span
                    className={`mb-badge mb-badge-${row.trust}`}
                    title={
                      row.trust === "reported"
                        ? "Owner-submitted results; see Details for the evaluation protocol and harness."
                        : undefined
                    }
                  >
                    {TRUST_LABELS[row.trust]}
                  </span>
                </td>
                <td className="lb-number">
                  {new Date(
                    row.finished_at ?? row.started_at,
                  ).toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function ModelBoardPage({ source = fixtureSource }: { source?: LeaderboardSource }) {
  const [models, setModels] = useState<BoardRow[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    source.load().then(({ models }) => { if (active) { setModels(models); setStatus("ready"); } }, () => { if (active) setStatus("error"); });
    return () => { active = false; };
  }, [source, attempt]);
  const [category, setCategory] = useState<Category>("en");
  const [size, setSize] = useState<SizeKey>("all");
  const [hideReported, setHideReported] = useState(false);
  const [axis, setAxis] = useState<RankAxis>("eff");
  const [sort, setSort] = useState<{ key: SortKey; direction: Direction }>({
    key: rankKey("en"),
    direction: NATURAL_DIRECTION[rankKey("en")],
  });
  const inCategory = filterRows(models, {
    category,
    size: "all",
    hideReported,
  });
  const visible = filterRows(models, { category, size, hideReported });
  const rows = sortRows(visible, sort.key, sort.direction);
  const ranks = rankRows(visible, category, axis);
  const rankedKey = rankKey(category, axis);
  const columns = SCORE_COLUMNS[category];
  const showDagger = visible.some((row) =>
    columns.some((column) => daggered(row, column)),
  );
  const chooseCategory = (next: Category) => {
    setCategory(next);
    setSort({
      key: rankKey(next, axis),
      direction: NATURAL_DIRECTION[rankKey(next, axis)],
    });
  };
  const chooseAxis = (next: RankAxis) => {
    setAxis(next);
    setSort({
      key: rankKey(category, next),
      direction: NATURAL_DIRECTION[rankKey(category, next)],
    });
  };
  return (
    <>
      <PageTop
        description={
          <p>
            Each row is the checkpoint its owner marked as the result, scored
            at exactly that training step, or the latest checkpoint the track
            evaluated itself.
          </p>
        }
      />
      <div className="leaderboard-page model-board">
      {status === "error" ? (
        <div className="lb-empty" role="alert">
          <h2>Results could not be loaded.</h2>
          <button className="secondary" onClick={() => { setStatus("loading"); setAttempt(attempt + 1); }}>
            Try again
          </button>
        </div>
      ) : status === "loading" ? (
        <div className="lb-empty" role="status">
          Loading model results…
        </div>
      ) : (
        <>
          <div className="mb-tabs" role="group" aria-label="Language">
            {(Object.keys(CATEGORY_LABELS) as Category[]).map((item) => (
              <button
                key={item}
                aria-label={CATEGORY_LABELS[item]}
                aria-pressed={category === item}
                onClick={() => chooseCategory(item)}
              >
                {CATEGORY_LABELS[item]}
                <small>
                  {
                    models.filter((row) => row.categories.includes(item))
                      .length
                  }
                </small>
              </button>
            ))}
          </div>
          <p className="lb-group-note">
            {category === "en" && axis === "overall" ? EN_OVERALL_NOTE : CATEGORY_NOTES[category]}
          </p>
          <div className="mb-controls">
            <div className="mb-sizes" role="group" aria-label="Model size">
              <button
                aria-pressed={size === "all"}
                onClick={() => setSize("all")}
              >
                All sizes <small>{inCategory.length}</small>
              </button>
              {SIZE_BUCKETS.map((bucket) => (
                <button
                  key={bucket.key}
                  title={bucket.range}
                  aria-pressed={size === bucket.key}
                  onClick={() => setSize(bucket.key)}
                >
                  {bucket.label}{" "}
                  <small>
                    {
                      inCategory.filter(
                        (row) => sizeBucket(row.n_params) === bucket.key,
                      ).length
                    }
                  </small>
                </button>
              ))}
            </div>
            <label className="mb-toggle">
              <input
                type="checkbox"
                checked={hideReported}
                onChange={(event) => setHideReported(event.target.checked)}
              />
              Hide self-reported
            </label>
            {category === "en" && (
              <div className="mb-sizes" role="group" aria-label="Ranking">
                Ranking:
                <button
                  aria-pressed={axis === "eff"}
                  onClick={() => chooseAxis("eff")}
                >
                  eff
                </button>
                <button
                  aria-pressed={axis === "overall"}
                  onClick={() => chooseAxis("overall")}
                >
                  Overall
                </button>
              </div>
            )}
          </div>
          <div className="lb-results-heading">
            <div>
              <span className="lb-eyebrow">
                {CATEGORY_LABELS[category]} results
              </span>
              <p>
                {rows.length} {rows.length === 1 ? "model" : "models"}
              </p>
            </div>

          </div>
          {!rows.length ? (
            <div className="lb-empty">
              <h2>No models in this view yet.</h2>
              <p>
                A finished public run appears here once it publishes its board
                metrics and marks its final checkpoint, or once the track has
                evaluated it.
              </p>
            </div>
          ) : (
            <BoardTable
              rows={rows}
              category={category}
              rankedKey={rankedKey}
              columns={columns}
              ranks={ranks}
              sort={sort}
              onSort={(key) =>
                setSort((current) => ({
                  key,
                  direction:
                    current.key === key
                      ? current.direction === "asc"
                        ? "desc"
                        : "asc"
                      : NATURAL_DIRECTION[key],
                }))
              }
            />
          )}
          {rows.length > 0 && showDagger && (
            <p className="lb-footnote">
              † measured by us with our protocol; may differ from the authors'
              own evaluation
            </p>
          )}
          <p className="lb-footnote mb-caveat">
            These are synthetic test data illustrating the Glint Tiny-ML protocol, not
            official leaderboard results. eff depends on the Glint min/max
            ranges at the revision shown. Self-reported rows use the authors'
            own protocols. Rows measured by track use the server's own
            evaluation of each public run's latest checkpoint.
          </p>
        </>
      )}
    </div>
    </>
  );
}
