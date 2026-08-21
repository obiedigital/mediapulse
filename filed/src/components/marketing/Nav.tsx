import { Link } from 'react-router-dom';
import { FolderCog, Menu, X } from 'lucide-react';
import { useState } from 'react';

const LINKS = [
  { href: '#platform', label: 'Platform' },
  { href: '#industries', label: 'Industries' },
  { href: '#how', label: 'How it works' },
  { href: '#pricing', label: 'Pricing' },
];

export function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="sticky top-0 z-50 border-b border-line/70 bg-paper/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between px-5 py-4 md:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-800">
            <FolderCog size={17} className="text-gold-400" />
          </div>
          <span className="font-display text-[16px] font-extrabold text-ink">Filed</span>
        </Link>

        <div className="hidden md:flex items-center gap-8 text-[13.5px] font-medium text-ink/60">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="hover:text-ink transition-colors">
              {l.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <Link to="/login" className="text-[13px] font-semibold text-ink/70 hover:text-ink px-3 py-2">
            Sign in
          </Link>
          <Link
            to="/login"
            className="rounded-lg bg-navy-800 px-4 py-2.5 text-[13px] font-semibold text-white hover:bg-navy-700 transition-colors"
          >
            Start free trial
          </Link>
        </div>

        <button className="md:hidden text-ink" onClick={() => setOpen((o) => !o)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-line bg-surface px-5 py-4 flex flex-col gap-3">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="text-[14px] font-medium text-ink/70">
              {l.label}
            </a>
          ))}
          <Link to="/login" className="mt-2 rounded-lg bg-navy-800 px-4 py-2.5 text-center text-[13px] font-semibold text-white">
            Start free trial
          </Link>
        </div>
      )}
    </nav>
  );
}
