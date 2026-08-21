import { useMemo, useState } from 'react';
import {
  Folder,
  FolderOpen,
  Search,
  Upload,
  FileText,
  FileImage,
  FileSpreadsheet,
  Mail,
  Star,
  Download,
  Share2,
  History,
  Lock,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { EmptyState } from '../../components/ui/EmptyState';
import { documents, folders } from '../../data/mockData';
import type { DocumentItem, DocStatus, DocType } from '../../types';
import { useToast } from '../../context/ToastContext';

const TYPE_ICON: Record<DocType, typeof FileText> = {
  pdf: FileText,
  image: FileImage,
  doc: FileText,
  xlsx: FileSpreadsheet,
  email: Mail,
};

const STATUS_TONE: Record<DocStatus, 'ok' | 'warn' | 'neutral'> = {
  active: 'ok',
  'pending-review': 'warn',
  archived: 'neutral',
};

function formatSize(kb: number) {
  return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
}

function buildTree(parentId: string | null) {
  return folders.filter((f) => f.parentId === parentId);
}

function FolderTree({ activeId, onSelect, parentId, depth }: { activeId: string; onSelect: (id: string) => void; parentId: string | null; depth: number }) {
  const children = buildTree(parentId);
  if (!children.length) return null;
  return (
    <div className="flex flex-col">
      {children.map((f) => {
        const isActive = f.id === activeId;
        return (
          <div key={f.id}>
            <button
              onClick={() => onSelect(f.id)}
              style={{ paddingLeft: 10 + depth * 14 }}
              className={`flex w-full items-center gap-2 rounded-lg py-2 pr-2 text-left text-[12.5px] transition-colors ${
                isActive ? 'bg-navy-50 font-semibold text-navy-800' : 'text-ink/65 hover:bg-paper-dim'
              }`}
            >
              {isActive ? <FolderOpen size={14} className="shrink-0" /> : <Folder size={14} className="shrink-0" />}
              <span className="flex-1 truncate">{f.name}</span>
              <span className="text-[10.5px] text-ink/35">{f.docCount || ''}</span>
            </button>
            <FolderTree activeId={activeId} onSelect={onSelect} parentId={f.id} depth={depth + 1} />
          </div>
        );
      })}
    </div>
  );
}

function folderPath(id: string): string {
  const f = folders.find((x) => x.id === id);
  if (!f) return '';
  if (!f.parentId) return f.name;
  return `${folderPath(f.parentId)} / ${f.name}`;
}

function descendantIds(id: string): string[] {
  const children = folders.filter((f) => f.parentId === id);
  return [id, ...children.flatMap((c) => descendantIds(c.id))];
}

export function DocumentManager() {
  const { push } = useToast();
  const [activeFolder, setActiveFolder] = useState('f-root');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<DocStatus | 'all'>('all');
  const [selected, setSelected] = useState<DocumentItem | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const visibleIds = useMemo(() => new Set(descendantIds(activeFolder)), [activeFolder]);

  const filtered = documents.filter((d) => {
    if (!visibleIds.has(d.folderId)) return false;
    if (statusFilter !== 'all' && d.status !== statusFilter) return false;
    if (query && !d.name.toLowerCase().includes(query.toLowerCase()) && !d.tags.some((t) => t.toLowerCase().includes(query.toLowerCase()))) return false;
    return true;
  });

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[240px_1fr]">
      <Card className="h-fit p-3 lg:sticky lg:top-24">
        <p className="px-2 pb-2 pt-1 text-[10px] font-bold uppercase tracking-wide text-ink/40">Folders</p>
        <FolderTree activeId={activeFolder} onSelect={setActiveFolder} parentId={null} depth={0} />
      </Card>

      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-ink/45">
          {folderPath(activeFolder).split(' / ').map((seg, i, arr) => (
            <span key={i} className="flex items-center gap-2">
              <span className={i === arr.length - 1 ? 'font-semibold text-ink' : ''}>{seg}</span>
              {i < arr.length - 1 && <ChevronRight size={12} />}
            </span>
          ))}
        </div>

        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-1 min-w-[220px] items-center gap-2 rounded-lg border border-line bg-paper px-3 py-2">
              <Search size={14} className="text-ink/40" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents or tags…"
                className="w-full bg-transparent text-[13px] outline-none placeholder:text-ink/35"
              />
            </div>
            <div className="flex gap-1.5">
              {(['all', 'active', 'pending-review', 'archived'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`rounded-full border px-3 py-1.5 text-[11.5px] font-medium transition-colors ${
                    statusFilter === s ? 'border-navy-700 bg-navy-800 text-white' : 'border-line text-ink/55 hover:bg-paper-dim'
                  }`}
                >
                  {s === 'all' ? 'All' : s === 'pending-review' ? 'Pending review' : s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
            <Button size="sm" icon={<Upload size={14} />} onClick={() => setUploadOpen(true)}>
              Upload
            </Button>
          </div>
        </Card>

        <Card className="overflow-hidden">
          {filtered.length === 0 ? (
            <EmptyState icon={<FileText size={22} />} title="No documents match" subtitle="Try a different folder, filter or search term." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[12.5px]">
                <thead>
                  <tr className="border-b border-line-soft text-left text-[10.5px] font-semibold uppercase tracking-wide text-ink/40">
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Owner</th>
                    <th className="px-4 py-3">Updated</th>
                    <th className="px-4 py-3">Size</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((d) => {
                    const Icon = TYPE_ICON[d.type];
                    return (
                      <tr
                        key={d.id}
                        onClick={() => setSelected(d)}
                        className="cursor-pointer border-b border-line-soft last:border-0 hover:bg-paper-dim/60"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-navy-50 text-navy-700">
                              <Icon size={14} />
                            </span>
                            <div className="min-w-0">
                              <p className="flex items-center gap-1.5 truncate font-medium text-ink">
                                {d.starred && <Star size={11} className="shrink-0 fill-gold-500 text-gold-500" />}
                                {d.name}
                              </p>
                              <div className="mt-0.5 flex gap-1.5">
                                {d.tags.slice(0, 2).map((t) => (
                                  <span key={t} className="rounded bg-paper-dim px-1.5 py-0.5 text-[10px] text-ink/50">{t}</span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge tone={STATUS_TONE[d.status]}>{d.status.replace('-', ' ')}</Badge>
                        </td>
                        <td className="px-4 py-3 text-ink/65">{d.owner}</td>
                        <td className="px-4 py-3 text-ink/50">{new Date(d.updatedAt).toLocaleDateString('en-ZA', { day: '2-digit', month: 'short' })}</td>
                        <td className="px-4 py-3 text-ink/50">{formatSize(d.sizeKb)}</td>
                        <td className="px-4 py-3">
                          {d.compliance && (
                            <span className="flex items-center gap-1 text-[10.5px] font-semibold text-navy-700">
                              <ShieldCheck size={12} /> {d.compliance}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.name ?? ''}
        subtitle={selected ? `${folderPath(selected.folderId)}` : undefined}
        width="max-w-xl"
      >
        {selected && (
          <div>
            <div className="flex items-center gap-3 rounded-xl border border-line-soft bg-paper p-4">
              <span className="flex h-14 w-14 items-center justify-center rounded-lg bg-navy-50 text-navy-700">
                {(() => {
                  const Icon = TYPE_ICON[selected.type];
                  return <Icon size={22} />;
                })()}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-semibold text-ink">{selected.name}</p>
                <p className="text-[11.5px] text-ink/50">{formatSize(selected.sizeKb)} · Owned by {selected.owner}</p>
              </div>
              <Badge tone={STATUS_TONE[selected.status]}>{selected.status.replace('-', ' ')}</Badge>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-[12.5px]">
              <div>
                <p className="text-ink/40">Last updated</p>
                <p className="font-medium text-ink">{new Date(selected.updatedAt).toLocaleString('en-ZA')}</p>
              </div>
              <div>
                <p className="text-ink/40">Compliance</p>
                <p className="font-medium text-ink">{selected.compliance ? `${selected.compliance} tracked` : 'Not flagged'}</p>
              </div>
              <div className="col-span-2">
                <p className="text-ink/40 mb-1">Tags</p>
                <div className="flex flex-wrap gap-1.5">
                  {selected.tags.map((t) => (
                    <span key={t} className="rounded-full bg-navy-50 px-2.5 py-1 text-[11px] font-medium text-navy-800">{t}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-5 flex items-center gap-2 rounded-lg bg-navy-50 px-3 py-2.5 text-[11.5px] text-navy-800">
              <Lock size={13} /> Only Admin & {selected.owner.split(' ')[0]} can edit this document · view-only for others
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <Button size="sm" icon={<Download size={14} />} onClick={() => push(`${selected.name} downloaded`)}>Download</Button>
              <Button size="sm" variant="outline" icon={<Share2 size={14} />} onClick={() => push('Share link copied', 'info')}>Share</Button>
              <Button size="sm" variant="outline" icon={<History size={14} />} onClick={() => push('Version history opened', 'info')}>Version history</Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal open={uploadOpen} onClose={() => setUploadOpen(false)} title="Upload document" subtitle={`Filing into ${folderPath(activeFolder)}`}>
        <div className="rounded-xl border-2 border-dashed border-line bg-paper p-10 text-center">
          <Upload size={22} className="mx-auto mb-3 text-ink/30" />
          <p className="text-[13px] font-medium text-ink">Drag files here, or click to browse</p>
          <p className="mt-1 text-[11.5px] text-ink/45">PDF, JPG, PNG, DOCX, XLSX up to 25MB</p>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={() => setUploadOpen(false)}>Cancel</Button>
          <Button
            size="sm"
            onClick={() => {
              setUploadOpen(false);
              push('Document uploaded and queued for classification');
            }}
          >
            Upload (demo)
          </Button>
        </div>
      </Modal>
    </div>
  );
}
