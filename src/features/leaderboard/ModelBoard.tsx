import { useState } from "react";
import { Link } from "react-router";
import { benchmarkSuites } from "./suites";
import type { Metric } from "./suites";
import { EvaluationDetails } from "./EvaluationDetails";
import { PageTop } from "../../components/PageTop";
import { fixtureSource } from "../../data/fixture-source";
import type { LeaderboardSource } from "../../data/source";
import { useEffect } from "react";
import { compact, format } from "./format";
import {
  NATURAL_DIRECTION,
  SIZE_BUCKETS,
  TRUST_LABELS,
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

const CATEGORY_LABELS = Object.fromEntries(benchmarkSuites.map(s => [s.category, s.label]));
type Column = Pick<Metric, "key" | "label"> & Partial<Omit<Metric, "key" | "label">>;
/** A cell carries the dagger when it is our measurement of an external model. */
const daggered = (row: BoardRow, column: Column) =>
  !!column.dagger && measuredByUs(row) && sortValue(row, column.key) !== null;

function BoardTable({
  rows,
  category,
  suiteId,
  rankedKey,
  columns,
  ranks,
  sort,
  onSort,
}: {
  rows: BoardRow[];
  category: Category;
  suiteId: string;
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
        <caption className="sr-only">Synthetic legacy results. Rankings are not verified comparisons across scoring protocols.</caption>
        <thead>
          <tr>
            <th scope="col">Rank</th>
            <th scope="col">Model</th>
            {columns.map(header)}
            <th scope="col">Author</th>
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
                  <span className="scale-label">Scale: {row.scale_rev ?? "Unavailable"}</span>
                  <EvaluationDetails row={row} suiteId={suiteId} />
                </td>
                {columns.map((column) => {
                  const text =
                    format(sortValue(row, column.key), column.digits) +
                    (daggered(row, column) ? "†" : "");
                  return (
                    <td className={`lb-number ${column.key === rankedKey ? "primary-metric" : ""}`} key={column.key}>
                      {column.key === rankedKey ? (
                        <strong>{text}</strong>
                      ) : (
                        text
                      )}
                    </td>
                  );
                })}
                <td>{row.author ?? row.owner}</td>
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
  const [suiteId, setSuiteId] = useState(benchmarkSuites[0].id);
  const suite = benchmarkSuites.find(s => s.id === suiteId)!;
  const category = suite.category;
  const [showSecondary, setShowSecondary] = useState(false);
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
  const metrics = [suite.primary, ...suite.secondary];
  const primary = metrics.find(m => m.key === rankedKey) ?? suite.primary;
  const columns = [primary, ...(showSecondary ? metrics.filter(m => m.key !== primary.key) : [])];
  const showDagger = visible.some((row) =>
    columns.some((column) => daggered(row, column)),
  );
  const chooseSuite = (id: string) => {
    setSuiteId(id);
    const next = benchmarkSuites.find(s => s.id === id)!.category;
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
          <p>Explore model checkpoints, scores and provenance. <Link to="/methodology">How to read these results →</Link></p>
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
            {benchmarkSuites.map((item) => (
              <button
                key={item.id}
                aria-label={item.label}
                aria-pressed={suiteId === item.id}
                onClick={() => chooseSuite(item.id)}
              >
                {item.label}
                <small>
                  {
                    models.filter((row) => row.categories.includes(item.category))
                      .length
                  }
                </small>
              </button>
            ))}
          </div>
          <p className="lb-group-note">
            {suite.summary} <Link to={suite.documentation}>Metric guide →</Link>
          </p>
          <aside className="compatibility-note">Legacy fixture view · Protocol compatibility is unverified. Scales are labeled per row; do not treat mixed or unavailable scales as comparable measurements.</aside>
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
            <label className="mb-toggle"><input type="checkbox" checked={showSecondary} onChange={e => setShowSecondary(e.target.checked)} />Show secondary metrics</label>
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
              suiteId={suiteId}
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
          <p className="lb-footnote mb-caveat">Synthetic test data only · <Link to="/methodology">Scoring, trust and reproducibility limitations</Link></p>
        </>
      )}
    </div>
    </>
  );
}
