import { useState } from 'react';
import { CheckCircle2, GitBranch, Bell, FileEdit, Clock, ArrowRight, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { workflows, workflowInstances as seedInstances } from '../../data/mockData';
import type { InstanceStatus, WorkflowInstance, WorkflowStepType } from '../../types';
import { useToast } from '../../context/ToastContext';

const STEP_ICON: Record<WorkflowStepType, typeof GitBranch> = {
  approval: CheckCircle2,
  condition: GitBranch,
  notification: Bell,
  form: FileEdit,
};

const COLOR_TONE: Record<string, string> = {
  gold: 'bg-gold-100 text-gold-600',
  info: 'bg-info-100 text-info-600',
  ok: 'bg-ok-100 text-ok-600',
  danger: 'bg-danger-100 text-danger-600',
};

const INSTANCE_TONE: Record<InstanceStatus, 'info' | 'warn' | 'ok' | 'danger'> = {
  'in-progress': 'info',
  waiting: 'warn',
  approved: 'ok',
  rejected: 'danger',
};

export function Workflows() {
  const { push } = useToast();
  const [activeId, setActiveId] = useState(workflows[0].id);
  const [instances, setInstances] = useState<WorkflowInstance[]>(seedInstances);
  const active = workflows.find((w) => w.id === activeId)!;
  const activeInstances = instances.filter((i) => i.workflowId === activeId);

  const resolveInstance = (id: string, status: InstanceStatus) => {
    setInstances((prev) => prev.map((i) => (i.id === id ? { ...i, status } : i)));
    push(status === 'approved' ? 'Step approved — routed to next stage' : 'Step rejected and sent back to requester', status === 'approved' ? 'success' : 'warn');
  };

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[300px_1fr]">
      <div className="flex flex-col gap-3">
        {workflows.map((w) => (
          <button
            key={w.id}
            onClick={() => setActiveId(w.id)}
            className={`rounded-2xl border p-4 text-left transition-colors ${
              w.id === activeId ? 'border-navy-700 bg-navy-50' : 'border-line bg-surface hover:border-navy-600/30'
            }`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${COLOR_TONE[w.color]}`}>
                <GitBranch size={14} />
              </span>
              <Badge tone="neutral">{w.category}</Badge>
            </div>
            <h4 className="font-display text-[13.5px] font-bold text-ink">{w.name}</h4>
            <p className="mt-1 text-[11.5px] leading-relaxed text-ink/50 line-clamp-2">{w.description}</p>
            <div className="mt-3 flex items-center gap-4 text-[11px] text-ink/45">
              <span>{w.activeInstances} active</span>
              <span>{w.completedThisMonth} done / mo</span>
            </div>
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-5">
        <Card className="p-6">
          <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
            <div>
              <Badge tone="neutral">{active.category}</Badge>
              <h3 className="mt-2 font-display text-[18px] font-bold text-ink">{active.name}</h3>
              <p className="mt-1 max-w-lg text-[13px] text-ink/55">{active.description}</p>
            </div>
            <div className="flex gap-5 text-center">
              <div>
                <p className="font-display text-[20px] font-extrabold text-ink">{active.activeInstances}</p>
                <p className="text-[10.5px] text-ink/45">Active</p>
              </div>
              <div>
                <p className="font-display text-[20px] font-extrabold text-ink">{active.avgCompletionHrs}h</p>
                <p className="text-[10.5px] text-ink/45">Avg. time</p>
              </div>
              <div>
                <p className="font-display text-[20px] font-extrabold text-ink">{active.completedThisMonth}</p>
                <p className="text-[10.5px] text-ink/45">This month</p>
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-stretch gap-2 overflow-x-auto pb-2">
            {active.steps.map((step, i) => {
              const Icon = STEP_ICON[step.type];
              return (
                <div key={step.id} className="flex items-center gap-2">
                  <div className="w-44 shrink-0 rounded-xl border border-line bg-paper p-3.5">
                    <div className="mb-2 flex items-center gap-2">
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-navy-100 text-navy-800">
                        <Icon size={13} />
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wide text-ink/40">{step.type}</span>
                    </div>
                    <p className="text-[12.5px] font-semibold text-ink leading-tight">{step.name}</p>
                    {step.assignee && <p className="mt-1 text-[10.5px] text-ink/45">{step.assignee}</p>}
                  </div>
                  {i < active.steps.length - 1 && <ArrowRight size={16} className="shrink-0 text-ink/25" />}
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="p-5">
          <h4 className="mb-3 font-display text-[13.5px] font-bold text-ink">Active instances</h4>
          {activeInstances.length === 0 ? (
            <p className="py-8 text-center text-[12.5px] text-ink/45">No active instances for this workflow.</p>
          ) : (
            <div className="flex flex-col divide-y divide-line-soft">
              {activeInstances.map((inst) => (
                <div key={inst.id} className="flex flex-wrap items-center gap-3 py-3.5 first:pt-0 last:pb-0">
                  <div className="min-w-[220px] flex-1">
                    <p className="text-[13px] font-medium text-ink">{inst.documentName}</p>
                    <p className="flex items-center gap-1.5 text-[11px] text-ink/45">
                      <Clock size={11} /> Started {new Date(inst.startedAt).toLocaleDateString('en-ZA', { day: '2-digit', month: 'short' })} by {inst.requester}
                    </p>
                  </div>
                  <span className="text-[11.5px] text-ink/50">
                    Step {inst.currentStepIndex + 1}/{active.steps.length}: <b className="text-ink">{active.steps[inst.currentStepIndex]?.name}</b>
                  </span>
                  <Badge tone={INSTANCE_TONE[inst.status]}>{inst.waitingOn ? `Waiting: ${inst.waitingOn}` : inst.status}</Badge>
                  {inst.status === 'in-progress' && (
                    <div className="flex gap-1.5">
                      <Button size="sm" variant="outline" icon={<ThumbsUp size={13} />} onClick={() => resolveInstance(inst.id, 'approved')}>
                        Approve
                      </Button>
                      <Button size="sm" variant="ghost" icon={<ThumbsDown size={13} className="text-danger-600" />} onClick={() => resolveInstance(inst.id, 'rejected')}>
                        Reject
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
