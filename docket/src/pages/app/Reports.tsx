import { BarChart, Bar, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Download, ShieldCheck, FileWarning, Clock3 } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { documents, workflows, monthlyVolume, departmentBreakdown } from '../../data/mockData';
import { useToast } from '../../context/ToastContext';

export function Reports() {
  const { push } = useToast();
  const complianceCounts = { POPIA: 0, FICA: 0, FSCA: 0 };
  documents.forEach((d) => {
    if (d.compliance) complianceCounts[d.compliance] += 1;
  });
  const pendingReview = documents.filter((d) => d.status === 'pending-review').length;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[13px] text-ink/55">Reporting period: <b className="text-ink">1 – 21 August 2026</b></p>
        <Button size="sm" variant="outline" icon={<Download size={14} />} onClick={() => push('Report exported as PDF', 'info')}>
          Export report
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy-50 text-navy-700"><ShieldCheck size={16} /></span>
          <p className="mt-3 font-display text-[22px] font-extrabold text-ink">{complianceCounts.POPIA + complianceCounts.FICA + complianceCounts.FSCA}</p>
          <p className="text-[11px] text-ink/45">Documents under compliance tracking</p>
        </Card>
        <Card className="p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-warn-100 text-warn-600"><FileWarning size={16} /></span>
          <p className="mt-3 font-display text-[22px] font-extrabold text-ink">{pendingReview}</p>
          <p className="text-[11px] text-ink/45">Documents pending review</p>
        </Card>
        <Card className="p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-info-100 text-info-600"><Clock3 size={16} /></span>
          <p className="mt-3 font-display text-[22px] font-extrabold text-ink">
            {(workflows.reduce((a, w) => a + w.avgCompletionHrs, 0) / workflows.length).toFixed(1)}h
          </p>
          <p className="text-[11px] text-ink/45">Avg. workflow turnaround</p>
        </Card>
      </div>

      <Card className="p-5">
        <h3 className="mb-4 font-display text-[13.5px] font-bold text-ink">Documents filed by department</h3>
        <div style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departmentBreakdown} margin={{ left: -20, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} stroke="#F0ECE1" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10.5, fill: '#8A8578' }} interval={0} angle={-12} textAnchor="end" height={50} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8A8578' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #E8E2D4', fontSize: 12 }} cursor={{ fill: '#F3EFE6' }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {departmentBreakdown.map((d) => (
                  <Cell key={d.name} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="mb-4 font-display text-[13.5px] font-bold text-ink">Scanning volume trend</h3>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyVolume} margin={{ left: -20, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} stroke="#F0ECE1" />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8A8578' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#8A8578' }} />
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #E8E2D4', fontSize: 12 }} cursor={{ fill: '#F3EFE6' }} />
              <Bar dataKey="scanned" fill="#D9A441" radius={[6, 6, 0, 0]} />
              <Bar dataKey="filed" fill="#1F2A52" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="mb-3 font-display text-[13.5px] font-bold text-ink">Workflow throughput by category</h3>
        <div className="flex flex-col divide-y divide-line-soft">
          {workflows.map((w) => (
            <div key={w.id} className="flex flex-wrap items-center gap-4 py-3 first:pt-0 last:pb-0">
              <div className="min-w-[200px] flex-1">
                <p className="text-[13px] font-medium text-ink">{w.name}</p>
                <p className="text-[11px] text-ink/45">{w.category}</p>
              </div>
              <Badge tone="neutral">{w.activeInstances} active</Badge>
              <span className="w-28 text-[12px] text-ink/55">{w.completedThisMonth} completed / mo</span>
              <span className="w-24 text-[12px] text-ink/55">{w.avgCompletionHrs}h avg.</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
