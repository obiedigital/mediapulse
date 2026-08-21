import { useState } from 'react';
import { Smartphone, Printer, Mail, UploadCloud, Loader2, CheckCircle2, FolderCheck, Sparkles } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ProgressBar } from '../../components/ui/Progress';
import { scanJobs as seedJobs } from '../../data/mockData';
import type { ScanJob, ScanStatus } from '../../types';
import { useToast } from '../../context/ToastContext';

const SOURCES = [
  { icon: Smartphone, name: 'Mobile App', desc: 'Snap a photo from the Filed app — auto-cropped and enhanced.' },
  { icon: Printer, name: 'Network Scanner', desc: 'Any office MFP scans straight into your cabinet over the network.' },
  { icon: Mail, name: 'Email Import', desc: 'Forward to your cabinet address and Filed extracts attachments.' },
  { icon: UploadCloud, name: 'Bulk Upload', desc: 'Drop hundreds of pages at once for overnight digitisation.' },
];

const STATUS_META: Record<ScanStatus, { label: string; tone: 'neutral' | 'info' | 'warn' | 'ok'; icon: typeof Loader2 }> = {
  queued: { label: 'Queued', tone: 'neutral', icon: Loader2 },
  processing: { label: 'Reading document…', tone: 'warn', icon: Sparkles },
  classified: { label: 'Classified', tone: 'info', icon: CheckCircle2 },
  filed: { label: 'Filed', tone: 'ok', icon: FolderCheck },
};

const SAMPLE_NAMES = ['IMG_20260821_1142.jpg', 'ScanSnap_Batch_0921.pdf', 'invoice_scan_0821.pdf', 'contract_scan_final.pdf'];
const SAMPLE_DEST = ['FICA & RICA', 'Supplier Invoices', 'Employment Contracts', 'Workshop & Service'];

export function SmartScan() {
  const { push } = useToast();
  const [jobs, setJobs] = useState<ScanJob[]>(seedJobs);
  const [simulating, setSimulating] = useState(false);

  const runSimulation = () => {
    if (simulating) return;
    setSimulating(true);
    const id = `sim-${Date.now()}`;
    const name = SAMPLE_NAMES[Math.floor(Math.random() * SAMPLE_NAMES.length)];
    const dest = SAMPLE_DEST[Math.floor(Math.random() * SAMPLE_DEST.length)];
    const job: ScanJob = {
      id,
      fileName: name,
      source: 'Mobile App',
      pages: Math.ceil(Math.random() * 5),
      status: 'queued',
      destinationFolder: dest,
      confidence: 0,
      submittedBy: 'You',
      submittedAt: new Date().toISOString(),
    };
    setJobs((prev) => [job, ...prev]);
    push(`${name} added to scan queue`, 'info');

    setTimeout(() => {
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status: 'processing' } : j)));
    }, 900);
    setTimeout(() => {
      const confidence = 90 + Math.floor(Math.random() * 9);
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status: 'classified', confidence } : j)));
      push(`Classified as "${dest}" (${confidence}% confidence)`, 'info');
    }, 2400);
    setTimeout(() => {
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status: 'filed' } : j)));
      push(`${name} filed into ${dest}`);
      setSimulating(false);
    }, 3800);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {SOURCES.map((s) => (
          <Card key={s.name} className="p-5">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gold-100 text-gold-600">
              <s.icon size={18} />
            </div>
            <h4 className="font-display text-[13.5px] font-bold text-ink">{s.name}</h4>
            <p className="mt-1 text-[12px] leading-relaxed text-ink/55">{s.desc}</p>
          </Card>
        ))}
      </div>

      <Card className="overflow-hidden">
        <div className="relative overflow-hidden border-b border-line bg-navy-950 p-6">
          <div className="relative z-10 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-display text-[15px] font-bold text-white">Capture simulator</h3>
              <p className="mt-1 max-w-md text-[12.5px] text-white/50">
                Simulate a mobile scan: Filed reads the page, classifies it, and files it into the right folder — no manual filing.
              </p>
            </div>
            <Button variant="secondary" icon={<Smartphone size={15} />} onClick={runSimulation} disabled={simulating}>
              {simulating ? 'Scanning…' : 'Simulate mobile scan'}
            </Button>
          </div>
          {simulating && (
            <div className="pointer-events-none absolute inset-x-10 top-0 h-full">
              <div className="absolute left-0 right-0 h-16 bg-gradient-to-b from-gold-400/25 to-transparent animate-scan-sweep" />
            </div>
          )}
        </div>

        <div className="p-2">
          {jobs.map((j) => {
            const meta = STATUS_META[j.status];
            const StatusIcon = meta.icon;
            return (
              <div key={j.id} className="flex flex-wrap items-center gap-4 border-b border-line-soft px-4 py-3.5 last:border-0">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-paper-dim text-ink/60">
                  <StatusIcon size={16} className={j.status === 'processing' ? 'animate-spin' : ''} />
                </span>
                <div className="min-w-[180px] flex-1">
                  <p className="truncate text-[13px] font-medium text-ink">{j.fileName}</p>
                  <p className="text-[11px] text-ink/45">{j.source} · {j.pages} page{j.pages > 1 ? 's' : ''} · {j.submittedBy}</p>
                </div>

                <div className="w-40">
                  {j.status === 'processing' ? (
                    <ProgressBar value={65} tone="gold" />
                  ) : j.confidence > 0 ? (
                    <div>
                      <div className="mb-1 flex justify-between text-[10.5px] text-ink/45">
                        <span>Confidence</span>
                        <span className="font-semibold text-ink">{j.confidence}%</span>
                      </div>
                      <ProgressBar value={j.confidence} tone={j.confidence > 95 ? 'ok' : 'gold'} />
                    </div>
                  ) : (
                    <span className="text-[11px] text-ink/35">Waiting…</span>
                  )}
                </div>

                <div className="w-40 text-[12px] text-ink/55">→ {j.destinationFolder}</div>

                <Badge tone={meta.tone}>{meta.label}</Badge>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
