import { useState } from 'react';
import { Users, ShieldCheck, Bell, Plug, Trash2, UserPlus } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Avatar } from '../../components/ui/Avatar';
import { demoUsers } from '../../data/mockData';
import { useToast } from '../../context/ToastContext';

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className={`relative h-[22px] w-[38px] shrink-0 rounded-full transition-colors ${on ? 'bg-navy-800' : 'bg-line'}`}
    >
      <span className={`absolute top-[3px] h-4 w-4 rounded-full bg-white transition-all ${on ? 'left-[19px]' : 'left-[3px]'}`} />
    </button>
  );
}

const RETENTION_ROWS = [
  { label: 'FICA / RICA customer documents', years: 5, framework: 'FICA' },
  { label: 'Employment contracts & HR records', years: 3, framework: 'POPIA' },
  { label: 'SARS / VAT & financial records', years: 5, framework: 'SARS Tax Act' },
  { label: 'Insurance claims & correspondence', years: 5, framework: 'FSCA' },
];

export function Settings() {
  const { push } = useToast();
  const [popia, setPopia] = useState(true);
  const [twoFa, setTwoFa] = useState(true);
  const [digest, setDigest] = useState(true);
  const [autoFile, setAutoFile] = useState(true);

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.3fr_1fr]">
      <div className="flex flex-col gap-5">
        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 font-display text-[13.5px] font-bold text-ink"><Users size={16} /> Users & roles</h3>
            <Button size="sm" icon={<UserPlus size={14} />} onClick={() => push('Invitation sent', 'info')}>Invite user</Button>
          </div>
          <div className="flex flex-col divide-y divide-line-soft">
            {demoUsers.map((u) => (
              <div key={u.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <Avatar initials={u.initials} color={u.color} size={32} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-medium text-ink">{u.name}</p>
                  <p className="truncate text-[11.5px] text-ink/45">{u.email} · {u.department}</p>
                </div>
                <Badge tone={u.role === 'Admin' ? 'navy' : u.role === 'Manager' ? 'gold' : 'neutral'}>{u.role}</Badge>
                <button className="text-ink/30 hover:text-danger-600"><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 flex items-center gap-2 font-display text-[13.5px] font-bold text-ink"><ShieldCheck size={16} /> Document retention rules</h3>
          <div className="flex flex-col divide-y divide-line-soft">
            {RETENTION_ROWS.map((r) => (
              <div key={r.label} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-medium text-ink">{r.label}</p>
                  <p className="text-[11px] text-ink/45">Aligned to {r.framework}</p>
                </div>
                <Badge tone="navy">{r.years} years</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 flex items-center gap-2 font-display text-[13.5px] font-bold text-ink"><Plug size={16} /> Integrations</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {['Sage Payroll', 'Outlook / Microsoft 365', 'DocFusion Scanners', 'SARS eFiling'].map((name) => (
              <div key={name} className="flex items-center justify-between rounded-xl border border-line bg-paper px-3.5 py-3">
                <span className="text-[12.5px] font-medium text-ink">{name}</span>
                <Badge tone="ok">Connected</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="flex flex-col gap-5">
        <Card className="p-5">
          <h3 className="mb-4 font-display text-[13.5px] font-bold text-ink">Compliance & security</h3>
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[13px] font-medium text-ink">POPIA consent tracking</p>
                <p className="text-[11.5px] text-ink/45">Log consent capture for every customer document.</p>
              </div>
              <Toggle on={popia} onChange={setPopia} />
            </div>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[13px] font-medium text-ink">Require two-factor authentication</p>
                <p className="text-[11.5px] text-ink/45">Enforced for Admin and Manager roles.</p>
              </div>
              <Toggle on={twoFa} onChange={setTwoFa} />
            </div>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[13px] font-medium text-ink">Auto-file classified scans</p>
                <p className="text-[11.5px] text-ink/45">Skip manual review above 95% confidence.</p>
              </div>
              <Toggle on={autoFile} onChange={setAutoFile} />
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 flex items-center gap-2 font-display text-[13.5px] font-bold text-ink"><Bell size={16} /> Notifications</h3>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[13px] font-medium text-ink">Daily digest email</p>
              <p className="text-[11.5px] text-ink/45">Pending approvals & scan queue, every morning at 7am.</p>
            </div>
            <Toggle on={digest} onChange={setDigest} />
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="mb-1 font-display text-[13.5px] font-bold text-ink">Plan</h3>
          <p className="text-[12.5px] text-ink/55">Business · billed annually</p>
          <p className="mt-3 font-display text-[24px] font-extrabold text-ink">R1,190 <span className="text-[12px] font-medium text-ink/45">/ user / month</span></p>
          <Button variant="outline" size="sm" className="mt-4 w-full justify-center" onClick={() => push('Opening billing portal…', 'info')}>
            Manage billing
          </Button>
        </Card>
      </div>
    </div>
  );
}
