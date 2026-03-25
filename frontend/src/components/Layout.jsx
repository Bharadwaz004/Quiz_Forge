import { Link, useLocation } from 'react-router-dom';
import { Zap, BookOpen, Users } from 'lucide-react';

export default function Layout({ children }) {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      {/* ─── Header ─── */}
      <header className="border-b border-surface-300/10 bg-surface-950/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
              <Zap className="w-5 h-5 text-accent" />
            </div>
            <span className="font-display font-bold text-lg text-surface-50 tracking-tight">
              QuizForge
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/organize" active={pathname === '/organize'}>
              <BookOpen className="w-4 h-4" />
              <span>Organize</span>
            </NavLink>
            <NavLink to="/play" active={pathname === '/play'}>
              <Users className="w-4 h-4" />
              <span>Play</span>
            </NavLink>
          </nav>
        </div>
      </header>

      {/* ─── Main ─── */}
      <main className="flex-1">
        {children}
      </main>

      {/* ─── Footer ─── */}
      <footer className="border-t border-surface-300/5 py-6">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-xs text-surface-300/40">
          <span>QuizForge — RAG-Powered Quiz Platform</span>
          <span className="font-mono">v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}

function NavLink({ to, active, children }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-display font-medium transition-all duration-200
        ${active
          ? 'bg-accent/10 text-accent border border-accent/20'
          : 'text-surface-300 hover:text-surface-100 hover:bg-surface-900'
        }`}
    >
      {children}
    </Link>
  );
}
