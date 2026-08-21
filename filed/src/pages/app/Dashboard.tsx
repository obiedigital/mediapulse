import { Link } from 'react-router-dom';
import { AreaChart, Area, ResponsiveContainer, XAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import {
  FolderOpen,
  ScanLine,
  Workflow,
  FileSignature,
  ArrowUpRight,
  ArrowRight,
  Upload,
  CheckCircle2,
  PenLine,
  Share2,
  Trash2,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ProgressBar } from '../../components/ui/Progress';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';
import {
  activity,
  departmentBreakdown,
  monthlyVolume,
  storageStats,
  workflowInstances,
  workflows,
  scanJobs,
} from '../../data/mockData';

const ACTIVITY_ICON = {
  upload: Upload,
  scan: ScanLine,
  approve: CheckCircle2,
  sign: PenLine,
  workflow: Workflow,
  share: Share2,
  delete: Trash2,
};

export function Dashboard() {
  const { user } = useAuth();
  const pendingApprovals = workflowInstances.filter((i) => i.status === 'in-progress' || i.status === 'waiting');
  const activeScans = scanJobs.filter((s) => s.status !== 'filed');

  const stats = [
    { label: 'Documents on file', value: storageStats.documentsTotal.toLocaleString(), delta: `+${storageStats.documentsThisMonth} this month`, up: true, icon: FolderOpen },
    { label: 'Pages scanned (Aug)', value: storageStats.pagesScannedThisMonth.toLocaleString(), delta: '+11% vs Jul', up: true, icon: ScanLine },
    { label: 'Awaiting your action', value: String(pendingApprovals.length + activeScans.length), delta: 'Across workflows & scans', up: false, icon: Workflow },
    { label: 'Signatures pending', value: '3', delta: '1 overdue', up: false, icon: FileSignature },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-[15px] font-bold text-ink">Welcome back, {user?.name.split(' ')[0]}</h2>
          <p className="text-[12.5px] text-ink/50">Thursday, 21 August 2026 · Rand Auto Group cabinet</p>
        </div>
        <div className="flex gap-2">
          <Link to="/app/scan">
            <Button variant="secondary" size="sm" icon={<ScanLine size={14} />}>New scan</Button>
          </Link>
          <Link to="/app/documents">
            <Button variant="outline" size="sm" icon={<Upload size={14} />}>Upload document</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label} className="p-4">
            <div className="flex items-center justify-between">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-50 text-navy-700">
                <s.icon size={15} />
              </span>
              {s.up && <ArrowUpRight size={14} className="text-ok-600" />}
            </div>
            <p className="mt-3 font-display text-[22px] font-extrabold text-ink">{s.value}</p>
            <p className="text-[11px] text-ink/45">{s.label}</p>
            <p className={`mt-1 text-[10.5px] font-medium ${s.up ? 'text-ok-600' : 'text-ink/40'}`}>{s.delta}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-display text-[13.5px] font-bold text-ink">Scan & filing volume</h3>
            <div className="flex items-center gap-3 text-[11px] text-ink/45">
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-gold-500" /> Scanned</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-navy-700" /> Filed</span>
            </div>
          </div>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyVolume} margin={{ left: -20, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="scannedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D9A441" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#D9A441" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="filedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2E3B72" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#2E3B72" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8A8578' }} />
                <Tooltip
                  contentStyle={{ borderRadius: 10, border: '1px solid #E8E2D4', fontSize: 12 }}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Area type="monotone" dataKey="scanned" stroke="#D9A441" strokeWidth={2} fill="url(#scannedGrad)" />
                <Area type="monotone" dataKey="filed" stroke="#2E3B72" strokeWidth={2} fill="url(#filedGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 font-display text-[13.5px] font-bold text-ink">Storage by department</h3>
          <div style={{ height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={departmentBreakdown} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70} paddingAngle={2}>
                  {departmentBreakdown.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #E8E2D4', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-1 flex flex-col gap-1.5">
            {departmentBreakdown.map((d) => (
              <div key={d.name} className="flex items-center justify-between text-[11.5px]">
                <span className="flex items-center gap-1.5 text-ink/60">
                  <span className="h-2 w-2 rounded-full" style={{ background: d.color }} /> {d.name}
                </span>
                <span className="font-medium text-ink">{d.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-display text-[13.5px] font-bold text-ink">Waiting on approval</h3>
            <Link to="/app/workflows" className="flex items-center gap-1 text-[12px] font-semibold text-navy-700 hover:underline">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          <div className="flex flex-col divide-y divide-line-soft">
            {pendingApprovals.map((inst) => {
              const wf = workflows.find((w) => w.id === inst.workflowId)!;
              return (
                <div key={inst.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-navy-50 text-navy-700">
                    <Workflow size={15} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-medium text-ink">{inst.documentName}</p>
                    <p className="text-[11.5px] text-ink/45">{wf.name} · step {inst.currentStepIndex + 1} of {wf.steps.length}</p>
                  </div>
                  <Badge tone={inst.status === 'waiting' ? 'warn' : 'info'}>{inst.waitingOn ?? inst.status}</Badge>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-display text-[13.5px] font-bold text-ink">Cabinet storage</h3>
          </div>
          <p className="font-display text-[24px] font-extrabold text-ink">
            {storageStats.usedGb} <span className="text-[13px] font-medium text-ink/45">/ {storageStats.limitGb} GB</span>
          </p>
          <div className="mt-3">
            <ProgressBar value={(storageStats.usedGb / storageStats.limitGb) * 100} tone="gold" />
          </div>
          <p className="mt-2 text-[11px] text-ink/45">Business plan · resets never — storage doesn't expire</p>

          <div className="mt-5 rounded-xl bg-ok-100/60 p-3.5">
            <p className="text-[12px] font-semibold text-ok-600">🌿 ~{storageStats.paperSavedReams} reams saved this month</p>
            <p className="mt-1 text-[11px] text-ink/50">Estimated vs. paper filing across all branches.</p>
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <h3 className="mb-3 font-display text-[13.5px] font-bold text-ink">Recent activity</h3>
        <div className="flex flex-col divide-y divide-line-soft">
          {activity.map((a) => {
            const Icon = ACTIVITY_ICON[a.kind];
            return (
              <div key={a.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-paper-dim text-ink/60">
                  <Icon size={14} />
                </span>
                <p className="min-w-0 flex-1 truncate text-[12.5px] text-ink/75">
                  <span className="font-semibold text-ink">{a.actor}</span> {a.action}{' '}
                  <span className="text-ink/55">{a.target}</span>
                </p>
                <span className="shrink-0 text-[11px] text-ink/40">{a.time}</span>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
