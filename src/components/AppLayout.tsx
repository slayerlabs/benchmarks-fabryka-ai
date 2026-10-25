import { NavLink, Outlet, useLocation } from "react-router";
import { useEffect, useRef } from "react";
export function AppLayout() {
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    document.title = `${pathname === "/models" ? "Leaderboard" : pathname === "/autoeval" ? "AutoEval" : pathname === "/benchmarks" ? "Benchmarks" : "Methodology"} · Fabryka Benchmarks`;
    main.current?.focus();
  }, [pathname]);
  return <div className="app-layout">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="app-header"><NavLink className="brand" to="/models">FABRYKA / BENCHMARKS</NavLink><span className="development-label">DEVELOPMENT VIEW</span>
      <nav aria-label="Main navigation">{[["/models","Leaderboard"],["/autoeval","AutoEval"],["/benchmarks","Benchmarks"],["/methodology","About / Methodology"]].map(([to,label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav>
    </header>
    <p className="fixture-banner" role="note">DEVELOPMENT FIXTURES · All models, scores and provenance below are synthetic test data. No production connection.</p>
    <main id="main" ref={main} tabIndex={-1}><Outlet /></main>
    <footer className="app-footer">Open methods. Clear results. <span>Fixture-only frontend · AutoEval execution is not connected.</span></footer>
  </div>;
}
