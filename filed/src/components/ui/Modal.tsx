import type { ReactNode } from 'react';
import { X } from 'lucide-react';

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  width = 'max-w-lg',
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  width?: string;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[200] flex items-start justify-center overflow-y-auto bg-navy-950/60 backdrop-blur-sm px-4 py-12"
      onClick={onClose}
    >
      <div
        className={`relative w-full ${width} rounded-2xl border border-line bg-surface p-6 shadow-2xl animate-fade-up`}
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute right-5 top-5 text-ink/40 hover:text-ink">
          <X size={18} />
        </button>
        <h3 className="font-display text-lg font-bold text-ink pr-6">{title}</h3>
        {subtitle && <p className="mt-1 text-[13px] text-ink/55">{subtitle}</p>}
        <div className="mt-5">{children}</div>
      </div>
    </div>
  );
}
