export type ModelInputResult = { ok: true; repository: string } | { ok: false; error: string };
/** Syntax only: never resolves revisions, inspects a repository or makes a request. */
export function parseModelInput(input: string): ModelInputResult {
  let repository = input.trim();
  const invalid = { ok: false as const, error: "Use owner/model or an HTTPS Hugging Face repository URL, without a revision path, query or fragment." };
  if (repository.startsWith("https://")) {
    try {
      const url = new URL(repository);
      if (url.hostname !== "huggingface.co" || url.username || url.password || url.port || url.search || url.hash) return invalid;
      repository = url.pathname.replace(/^\//, "").replace(/\/$/, "");
    } catch { return invalid; }
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(repository)) return invalid;
  return { ok: true, repository };
}
