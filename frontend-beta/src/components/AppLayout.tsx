import { NavLink, Outlet, useLocation } from "react-router";
import { useEffect, useRef } from "react";
import fabrykaMark from "../assets/fabryka-mark.svg";
export function AppLayout() {
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    document.title = `${pathname === "/models" ? "Leaderboard" : pathname === "/autoeval" ? "AutoEval" : pathname === "/benchmarks" ? "Benchmarks" : "Methodology"} · Fabryka Benchmarks`;
    main.current?.focus();
  }, [pathname]);
  return <div className="app-layout">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="app-header"><div className="app-brand-row"><NavLink className="brand brand-lockup" to="/models" aria-label="Fabryka Benchmarks home"><img src={fabrykaMark} width="40" height="40" alt="" /><span>fabryka<span className="brand-product"> / benchmarks</span></span></NavLink><span className="development-label">DEVELOPMENT VIEW</span></div>
      <nav aria-label="Main navigation">{[["/models","Leaderboard"],["/autoeval","AutoEval"],["/benchmarks","Benchmarks"],["/methodology","About / Methodology"]].map(([to,label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav>
    </header>
    <p className="fixture-banner" role="note">DEVELOPMENT VIEW · Leaderboard models, scores and evaluation provenance are synthetic test data. Catalog definitions are source references. No production connection.</p>
    <main id="main" ref={main} tabIndex={-1}><Outlet /></main>
    <footer className="app-footer">Open methods. Clear results. <span>Fixture-only frontend · AutoEval execution is not connected.</span></footer>
  </div>;
}
