import { FolderCog } from 'lucide-react';

const COLUMNS = [
  {
    title: 'Platform',
    links: ['Document Manager', 'Smart Scan', 'Workflow Automation', 'eSignature & Forms', 'Reporting'],
  },
  {
    title: 'Industries',
    links: ['Automotive Dealerships', 'HR & Payroll', 'Insurance & Broking', 'Finance & SARS Compliance'],
  },
  {
    title: 'Company',
    links: ['About', 'Security & POPIA', 'Customers', 'Contact'],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto max-w-[1240px] px-5 py-14 md:px-8">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-800">
                <FolderCog size={17} className="text-gold-400" />
              </div>
              <span className="font-display text-[15px] font-extrabold text-ink">Docket</span>
            </div>
            <p className="mt-3 max-w-xs text-[12.5px] leading-relaxed text-ink/55">
              The paperless office platform for South African business. Document management, smart scanning, workflow
              automation and eSignatures — in one secure cabinet.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h5 className="mb-3 text-[11px] font-bold uppercase tracking-wide text-ink/40">{col.title}</h5>
              <ul className="flex flex-col gap-2.5">
                {col.links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-[13px] text-ink/60 hover:text-ink">
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-6 text-[11.5px] text-ink/45">
          <span>© 2026 Docket Software (Pty) Ltd. Cape Town, South Africa.</span>
          <span>POPIA compliant · Hosted in ZA · Demo product — sample data only</span>
        </div>
      </div>
    </footer>
  );
}
