import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FolderCog, ArrowRight } from 'lucide-react';
import { demoUsers } from '../../data/mockData';
import { useAuth } from '../../context/AuthContext';
import { Avatar } from '../../components/ui/Avatar';
import { Button } from '../../components/ui/Button';

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const enter = (userId: string) => {
    login(userId);
    navigate('/app');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-5 py-12" style={{ backgroundImage: 'radial-gradient(circle at 25% 15%, rgba(217,164,65,.10), transparent 45%), radial-gradient(circle at 80% 85%, rgba(31,42,82,.08), transparent 50%)' }}>
      <div className="w-full max-w-[540px] rounded-2xl border border-line bg-surface p-9 shadow-xl shadow-navy-900/5">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-800">
            <FolderCog size={17} className="text-gold-400" />
          </div>
          <span className="font-display text-[15px] font-extrabold text-ink">Docket</span>
        </Link>

        <h1 className="mt-6 font-display text-[24px] font-extrabold text-ink">Welcome back</h1>
        <p className="mt-1 text-[13px] text-ink/55">This is a demo cabinet for Rand Auto Group. Pick a role to explore, or sign in below.</p>

        <div className="mt-6 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {demoUsers.map((u) => (
            <button
              key={u.id}
              onClick={() => enter(u.id)}
              className="flex items-center gap-3 rounded-xl border border-line bg-paper px-3.5 py-3 text-left transition-colors hover:border-gold-500 hover:bg-gold-50"
            >
              <Avatar initials={u.initials} color={u.color} size={34} />
              <div className="min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-wide text-navy-700">{u.role}</p>
                <p className="truncate text-[13px] font-semibold text-ink">{u.name}</p>
                <p className="truncate text-[11px] text-ink/45">{u.department}</p>
              </div>
            </button>
          ))}
        </div>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-line" />
          <span className="text-[11px] font-medium text-ink/40">or sign in manually</span>
          <div className="h-px flex-1 bg-line" />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            enter('u1');
          }}
        >
          <div className="mb-3.5">
            <label className="mb-1.5 block text-[11.5px] font-medium text-ink/55">Work email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.co.za"
              className="w-full rounded-lg border border-line bg-paper px-3.5 py-2.5 text-[13.5px] text-ink outline-none focus:border-navy-600"
            />
          </div>
          <div className="mb-5">
            <label className="mb-1.5 block text-[11.5px] font-medium text-ink/55">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border border-line bg-paper px-3.5 py-2.5 text-[13.5px] text-ink outline-none focus:border-navy-600"
            />
          </div>
          <Button type="submit" className="w-full justify-center" iconRight={<ArrowRight size={15} />}>
            Sign in to your cabinet
          </Button>
        </form>

        <p className="mt-6 text-center text-[11.5px] text-ink/40">
          Demo product — no real credentials required.{' '}
          <Link to="/" className="font-semibold text-navy-800 hover:underline">
            Back to site
          </Link>
        </p>
      </div>
    </div>
  );
}
