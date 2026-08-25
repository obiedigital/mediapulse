import { useState } from 'react';
import { FileSignature, Plus, ClipboardList, Users, Clock, Send } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { signatureRequests, formTemplates } from '../../data/mockData';
import type { SignatureStatus, SignerStatus } from '../../types';
import { useToast } from '../../context/ToastContext';

const STATUS_TONE: Record<SignatureStatus, 'neutral' | 'info' | 'warn' | 'ok' | 'danger'> = {
  draft: 'neutral',
  sent: 'info',
  'partially-signed': 'warn',
  completed: 'ok',
  declined: 'danger',
  expired: 'neutral',
};

const SIGNER_TONE: Record<SignerStatus, 'neutral' | 'info' | 'ok' | 'danger'> = {
  pending: 'neutral',
  viewed: 'info',
  signed: 'ok',
  declined: 'danger',
};

export function ESignature() {
  const { push } = useToast();
  const [newOpen, setNewOpen] = useState(false);
  const [tab, setTab] = useState<'signatures' | 'forms'>('signatures');

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1.5 rounded-lg border border-line bg-surface p-1">
          <button
            onClick={() => setTab('signatures')}
            className={`rounded-md px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors ${tab === 'signatures' ? 'bg-navy-800 text-white' : 'text-ink/55'}`}
          >
            Signature requests
          </button>
          <button
            onClick={() => setTab('forms')}
            className={`rounded-md px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors ${tab === 'forms' ? 'bg-navy-800 text-white' : 'text-ink/55'}`}
          >
            Form templates
          </button>
        </div>
        <Button size="sm" icon={<Plus size={14} />} onClick={() => setNewOpen(true)}>
          {tab === 'signatures' ? 'New signature request' : 'New form'}
        </Button>
      </div>

      {tab === 'signatures' ? (
        <div className="flex flex-col gap-3">
          {signatureRequests.map((r) => (
            <Card key={r.id} className="p-4">
              <div className="flex flex-wrap items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gold-100 text-gold-600">
                  <FileSignature size={17} />
                </span>
                <div className="min-w-[220px] flex-1">
                  <p className="text-[13.5px] font-semibold text-ink">{r.docName}</p>
                  <p className="text-[11.5px] text-ink/45">{r.template} · sent {new Date(r.createdAt).toLocaleDateString('en-ZA', { day: '2-digit', month: 'short' })} · due {r.dueDate}</p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {r.signers.map((s) => (
                    <span key={s.email} className="flex items-center gap-1">
                      <Badge tone={SIGNER_TONE[s.status]}>{s.name.split(' ')[0]} · {s.status}</Badge>
                    </span>
                  ))}
                </div>
                <Badge tone={STATUS_TONE[r.status]}>{r.status.replace('-', ' ')}</Badge>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {formTemplates.map((f) => (
            <Card key={f.id} className="p-5">
              <div className="mb-3 flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy-50 text-navy-700">
                  <ClipboardList size={16} />
                </span>
                <Badge tone="neutral">{f.category}</Badge>
              </div>
              <h4 className="font-display text-[13.5px] font-bold text-ink">{f.name}</h4>
              <div className="mt-3 flex items-center gap-4 text-[11.5px] text-ink/50">
                <span className="flex items-center gap-1"><ClipboardList size={12} /> {f.fields} fields</span>
                <span className="flex items-center gap-1"><Users size={12} /> {f.submissions} submissions</span>
              </div>
              <p className="mt-2 flex items-center gap-1 text-[11px] text-ink/40">
                <Clock size={11} /> Last used {new Date(f.lastUsed).toLocaleDateString('en-ZA', { day: '2-digit', month: 'short' })}
              </p>
              <Button variant="outline" size="sm" className="mt-4 w-full justify-center" onClick={() => push(`Opening "${f.name}" builder…`, 'info')}>
                Edit template
              </Button>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={newOpen}
        onClose={() => setNewOpen(false)}
        title={tab === 'signatures' ? 'New signature request' : 'New form template'}
        subtitle={tab === 'signatures' ? 'Send a document out for eSignature.' : 'Build a new intake or acknowledgement form.'}
      >
        <div className="flex flex-col gap-3.5">
          <div>
            <label className="mb-1.5 block text-[11.5px] font-medium text-ink/55">Document / template name</label>
            <input placeholder="e.g. Vehicle Sale Agreement" className="w-full rounded-lg border border-line bg-paper px-3.5 py-2.5 text-[13px] outline-none focus:border-navy-600" />
          </div>
          <div>
            <label className="mb-1.5 block text-[11.5px] font-medium text-ink/55">Recipient email</label>
            <input placeholder="name@example.co.za" className="w-full rounded-lg border border-line bg-paper px-3.5 py-2.5 text-[13px] outline-none focus:border-navy-600" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button
              size="sm"
              icon={<Send size={14} />}
              onClick={() => {
                setNewOpen(false);
                push(tab === 'signatures' ? 'Signature request sent' : 'Form template created');
              }}
            >
              {tab === 'signatures' ? 'Send for signature' : 'Create form'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
