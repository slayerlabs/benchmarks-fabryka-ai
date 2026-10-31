const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
export const format = (value: number | null | undefined, digits = 3) =>
  finite(value) ? value.toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits }) : "—";
export const compact = (value: number | null | undefined) =>
  finite(value) ? new Intl.NumberFormat("en-US", { notation: value >= 1e12 ? "scientific" : "compact", maximumFractionDigits: 1 }).format(value) : "—";
