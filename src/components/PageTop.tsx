import type { ReactNode } from "react";
export function PageTop({ title = "Model Leaderboard", description }: { title?: string; description: ReactNode }) {
  return <header className="page-top"><h1>{title}</h1>{description}</header>;
}
