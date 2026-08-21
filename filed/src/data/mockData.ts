import type {
  DemoUser,
  FolderNode,
  DocumentItem,
  ScanJob,
  WorkflowDef,
  WorkflowInstance,
  SignatureRequest,
  FormTemplate,
  ActivityItem,
} from '../types';

export const ORG_NAME = 'Rand Auto Group';

export const demoUsers: DemoUser[] = [
  {
    id: 'u1',
    name: 'Naledi Mokoena',
    role: 'Admin',
    department: 'IT & Compliance',
    org: ORG_NAME,
    email: 'naledi@randauto.co.za',
    initials: 'NM',
    color: 'bg-navy-800',
  },
  {
    id: 'u2',
    name: 'Johan Pretorius',
    role: 'Manager',
    department: 'Dealership Operations',
    org: ORG_NAME,
    email: 'johan@randauto.co.za',
    initials: 'JP',
    color: 'bg-gold-600',
  },
  {
    id: 'u3',
    name: 'Thandiwe Nkosi',
    role: 'Staff',
    department: 'HR & Payroll',
    org: ORG_NAME,
    email: 'thandiwe@randauto.co.za',
    initials: 'TN',
    color: 'bg-info-600',
  },
  {
    id: 'u4',
    name: 'Riaan de Wet',
    role: 'Staff',
    department: 'Finance',
    org: ORG_NAME,
    email: 'riaan@randauto.co.za',
    initials: 'RW',
    color: 'bg-ok-600',
  },
];

export const folders: FolderNode[] = [
  { id: 'f-root', name: 'Cabinet', parentId: null, docCount: 0 },
  { id: 'f-hr', name: 'HR & Payroll', parentId: 'f-root', docCount: 0 },
  { id: 'f-hr-contracts', name: 'Employment Contracts', parentId: 'f-hr', docCount: 0 },
  { id: 'f-hr-leave', name: 'Leave & Payslips', parentId: 'f-hr', docCount: 0 },
  { id: 'f-fin', name: 'Finance', parentId: 'f-root', docCount: 0 },
  { id: 'f-fin-invoices', name: 'Supplier Invoices', parentId: 'f-fin', docCount: 0 },
  { id: 'f-fin-vat', name: 'VAT & SARS', parentId: 'f-fin', docCount: 0 },
  { id: 'f-sales', name: 'Vehicle Sales', parentId: 'f-root', docCount: 0 },
  { id: 'f-sales-deals', name: 'Deal Files', parentId: 'f-sales', docCount: 0 },
  { id: 'f-sales-fica', name: 'FICA & RICA', parentId: 'f-sales', docCount: 0 },
  { id: 'f-service', name: 'Workshop & Service', parentId: 'f-root', docCount: 0 },
  { id: 'f-insurance', name: 'Insurance & Warranties', parentId: 'f-root', docCount: 0 },
  { id: 'f-compliance', name: 'Compliance', parentId: 'f-root', docCount: 0 },
];

export const documents: DocumentItem[] = [
  { id: 'd1', name: 'Deal File - VW Polo 2024 - B. Khumalo.pdf', folderId: 'f-sales-deals', type: 'pdf', sizeKb: 4820, owner: 'Johan Pretorius', updatedAt: '2026-08-20T09:12:00', tags: ['vehicle sale', 'signed'], status: 'active', starred: true },
  { id: 'd2', name: 'FICA Pack - S. Naidoo.pdf', folderId: 'f-sales-fica', type: 'pdf', sizeKb: 1210, owner: 'Johan Pretorius', updatedAt: '2026-08-20T08:44:00', tags: ['FICA', 'ID verified'], status: 'pending-review', compliance: 'FICA' },
  { id: 'd3', name: 'Employment Contract - T. Radebe.pdf', folderId: 'f-hr-contracts', type: 'pdf', sizeKb: 640, owner: 'Thandiwe Nkosi', updatedAt: '2026-08-19T14:02:00', tags: ['contract', 'new hire'], status: 'active', compliance: 'POPIA' },
  { id: 'd4', name: 'August Payslips - Batch.xlsx', folderId: 'f-hr-leave', type: 'xlsx', sizeKb: 210, owner: 'Thandiwe Nkosi', updatedAt: '2026-08-18T16:30:00', tags: ['payroll'], status: 'active' },
  { id: 'd5', name: 'Supplier Invoice - Bidvest Parts #88213.pdf', folderId: 'f-fin-invoices', type: 'pdf', sizeKb: 320, owner: 'Riaan de Wet', updatedAt: '2026-08-20T07:55:00', tags: ['invoice', 'parts'], status: 'pending-review' },
  { id: 'd6', name: 'VAT201 - July 2026.pdf', folderId: 'f-fin-vat', type: 'pdf', sizeKb: 180, owner: 'Riaan de Wet', updatedAt: '2026-08-15T11:20:00', tags: ['SARS', 'VAT'], status: 'active' },
  { id: 'd7', name: 'Service Job Card #10432 - Toyota Hilux.pdf', folderId: 'f-service', type: 'pdf', sizeKb: 540, owner: 'Workshop Team', updatedAt: '2026-08-20T10:05:00', tags: ['job card'], status: 'active' },
  { id: 'd8', name: 'Extended Warranty - Isuzu D-Max.pdf', folderId: 'f-insurance', type: 'pdf', sizeKb: 410, owner: 'Naledi Mokoena', updatedAt: '2026-08-17T13:40:00', tags: ['warranty'], status: 'active' },
  { id: 'd9', name: 'POPIA Consent Register.xlsx', folderId: 'f-compliance', type: 'xlsx', sizeKb: 95, owner: 'Naledi Mokoena', updatedAt: '2026-08-12T09:00:00', tags: ['POPIA', 'register'], status: 'active', compliance: 'POPIA' },
  { id: 'd10', name: 'Trade-In Valuation - Ford Ranger.pdf', folderId: 'f-sales-deals', type: 'pdf', sizeKb: 260, owner: 'Johan Pretorius', updatedAt: '2026-08-19T15:12:00', tags: ['valuation'], status: 'active' },
  { id: 'd11', name: 'Insurance Claim - Hail Damage Batch.pdf', folderId: 'f-insurance', type: 'pdf', sizeKb: 3100, owner: 'Naledi Mokoena', updatedAt: '2026-08-14T10:00:00', tags: ['FSCA', 'claim'], status: 'active', compliance: 'FSCA' },
  { id: 'd12', name: 'ID Copy - W. Botha.jpg', folderId: 'f-sales-fica', type: 'image', sizeKb: 1840, owner: 'Scan Queue', updatedAt: '2026-08-20T11:02:00', tags: ['FICA'], status: 'pending-review', compliance: 'FICA' },
  { id: 'd13', name: 'Leave Application - R. Dlamini.pdf', folderId: 'f-hr-leave', type: 'pdf', sizeKb: 88, owner: 'Thandiwe Nkosi', updatedAt: '2026-08-18T08:20:00', tags: ['leave'], status: 'active' },
  { id: 'd14', name: 'Fleet Insurance Renewal 2026.pdf', folderId: 'f-insurance', type: 'pdf', sizeKb: 720, owner: 'Naledi Mokoena', updatedAt: '2026-08-10T09:30:00', tags: ['renewal'], status: 'archived' },
];

for (const d of documents) {
  const folder = folders.find((f) => f.id === d.folderId);
  if (folder) folder.docCount += 1;
}

export const scanJobs: ScanJob[] = [
  { id: 's1', fileName: 'IMG_20260821_0731.jpg', source: 'Mobile App', pages: 3, status: 'classified', destinationFolder: 'FICA & RICA', confidence: 96, submittedBy: 'Johan Pretorius', submittedAt: '2026-08-21T07:31:00' },
  { id: 's2', fileName: 'ScanSnap_Batch_0912.pdf', source: 'Network Scanner', pages: 12, status: 'processing', destinationFolder: 'Supplier Invoices', confidence: 0, submittedBy: 'Riaan de Wet', submittedAt: '2026-08-21T09:12:00' },
  { id: 's3', fileName: 'payslip_scan_batch.pdf', source: 'Bulk Upload', pages: 34, status: 'queued', destinationFolder: 'Leave & Payslips', confidence: 0, submittedBy: 'Thandiwe Nkosi', submittedAt: '2026-08-21T09:40:00' },
  { id: 's4', fileName: 'contract_signed_scan.pdf', source: 'Email Import', pages: 6, status: 'filed', destinationFolder: 'Employment Contracts', confidence: 99, submittedBy: 'inbox@randauto.co.za', submittedAt: '2026-08-21T06:58:00' },
  { id: 's5', fileName: 'IMG_20260820_1604.jpg', source: 'Mobile App', pages: 1, status: 'filed', destinationFolder: 'Workshop & Service', confidence: 91, submittedBy: 'Workshop Team', submittedAt: '2026-08-20T16:04:00' },
];

export const workflows: WorkflowDef[] = [
  {
    id: 'w1',
    name: 'New Vehicle Deal Approval',
    description: 'Deal file, FICA pack and trade-in valuation routed for sales manager and finance sign-off before delivery.',
    category: 'Vehicle Sales',
    color: 'gold',
    activeInstances: 4,
    completedThisMonth: 61,
    avgCompletionHrs: 5.4,
    steps: [
      { id: 'st1', name: 'FICA & RICA check', type: 'condition', detail: 'Auto-verify ID document and proof of address against FICA rules.' },
      { id: 'st2', name: 'Sales Manager approval', type: 'approval', assignee: 'Johan Pretorius', detail: 'Reviews deal terms and trade-in valuation.' },
      { id: 'st3', name: 'Finance sign-off', type: 'approval', assignee: 'Riaan de Wet', detail: 'Confirms financing and VAT treatment.' },
      { id: 'st4', name: 'Notify delivery team', type: 'notification', detail: 'Emails workshop + delivery once approved.' },
    ],
  },
  {
    id: 'w2',
    name: 'New Employee Onboarding',
    description: 'Contract generation, eSignature and payroll setup for every new hire across dealership branches.',
    category: 'HR & Payroll',
    color: 'info',
    activeInstances: 2,
    completedThisMonth: 9,
    avgCompletionHrs: 18.2,
    steps: [
      { id: 'st1', name: 'Offer form submitted', type: 'form', detail: 'HR captures role, branch and salary band.' },
      { id: 'st2', name: 'Contract eSignature', type: 'approval', assignee: 'Candidate', detail: 'Sent for signature via Filed eSign.' },
      { id: 'st3', name: 'HR Manager approval', type: 'approval', assignee: 'Thandiwe Nkosi', detail: 'Confirms signed contract and ID documents.' },
      { id: 'st4', name: 'Notify payroll & IT', type: 'notification', detail: 'Auto-emails payroll system and IT for access setup.' },
    ],
  },
  {
    id: 'w3',
    name: 'Supplier Invoice Payment',
    description: 'Three-way match and approval chain for parts and services invoices above R5,000.',
    category: 'Finance',
    color: 'ok',
    activeInstances: 6,
    completedThisMonth: 143,
    avgCompletionHrs: 9.1,
    steps: [
      { id: 'st1', name: 'Amount check', type: 'condition', detail: 'Under R5,000 auto-approves; over routes to manager.' },
      { id: 'st2', name: 'Branch Manager approval', type: 'approval', assignee: 'Johan Pretorius', detail: 'Confirms PO and delivery note match.' },
      { id: 'st3', name: 'Finance sign-off', type: 'approval', assignee: 'Riaan de Wet', detail: 'Schedules payment run.' },
      { id: 'st4', name: 'Archive to VAT register', type: 'notification', detail: 'Files to Finance / VAT & SARS automatically.' },
    ],
  },
  {
    id: 'w4',
    name: 'Insurance Claim Intake',
    description: 'FSCA-aligned intake for hail, accident and theft claims across the fleet and customer vehicles.',
    category: 'Insurance',
    color: 'danger',
    activeInstances: 1,
    completedThisMonth: 22,
    avgCompletionHrs: 30.6,
    steps: [
      { id: 'st1', name: 'Claim form submitted', type: 'form', detail: 'Customer or staff captures incident details + photos.' },
      { id: 'st2', name: 'Compliance review', type: 'approval', assignee: 'Naledi Mokoena', detail: 'FSCA disclosure and documentation check.' },
      { id: 'st3', name: 'Insurer submission', type: 'notification', detail: 'Package emailed to underwriter.' },
    ],
  },
];

export const workflowInstances: WorkflowInstance[] = [
  { id: 'i1', workflowId: 'w1', documentName: 'Deal File - Isuzu D-Max - K. van Zyl', currentStepIndex: 1, status: 'in-progress', startedAt: '2026-08-21T08:10:00', requester: 'Johan Pretorius', waitingOn: 'Johan Pretorius' },
  { id: 'i2', workflowId: 'w1', documentName: 'Deal File - VW Polo Vivo - N. Zulu', currentStepIndex: 2, status: 'in-progress', startedAt: '2026-08-20T14:00:00', requester: 'Johan Pretorius', waitingOn: 'Riaan de Wet' },
  { id: 'i3', workflowId: 'w2', documentName: 'Onboarding - S. Mahlangu (Parts Advisor)', currentStepIndex: 1, status: 'waiting', startedAt: '2026-08-19T09:00:00', requester: 'Thandiwe Nkosi', waitingOn: 'S. Mahlangu (signature)' },
  { id: 'i4', workflowId: 'w3', documentName: 'Bidvest Parts #88213 — R8,240', currentStepIndex: 1, status: 'in-progress', startedAt: '2026-08-20T07:56:00', requester: 'Riaan de Wet', waitingOn: 'Johan Pretorius' },
  { id: 'i5', workflowId: 'w3', documentName: 'Midas Batch Invoice — R2,110', currentStepIndex: 3, status: 'approved', startedAt: '2026-08-18T10:00:00', requester: 'Riaan de Wet' },
  { id: 'i6', workflowId: 'w4', documentName: 'Hail Damage Claim — Fleet #22', currentStepIndex: 1, status: 'in-progress', startedAt: '2026-08-14T10:05:00', requester: 'Naledi Mokoena', waitingOn: 'Naledi Mokoena' },
];

export const signatureRequests: SignatureRequest[] = [
  {
    id: 'sig1',
    docName: 'Employment Contract - S. Mahlangu.pdf',
    template: 'Standard Employment Contract',
    signers: [{ name: 'S. Mahlangu', email: 's.mahlangu@gmail.com', status: 'viewed' }],
    status: 'sent',
    createdAt: '2026-08-19T09:05:00',
    dueDate: '2026-08-24',
  },
  {
    id: 'sig2',
    docName: 'Vehicle Sale Agreement - VW Polo Vivo.pdf',
    template: 'Vehicle Sale Agreement',
    signers: [
      { name: 'N. Zulu', email: 'n.zulu@outlook.com', status: 'signed' },
      { name: 'Johan Pretorius', email: 'johan@randauto.co.za', status: 'pending' },
    ],
    status: 'partially-signed',
    createdAt: '2026-08-20T14:05:00',
    dueDate: '2026-08-22',
  },
  {
    id: 'sig3',
    docName: 'Extended Warranty Addendum - Isuzu D-Max.pdf',
    template: 'Warranty Addendum',
    signers: [{ name: 'K. van Zyl', email: 'kvanzyl@icloud.com', status: 'pending' }],
    status: 'sent',
    createdAt: '2026-08-21T08:12:00',
    dueDate: '2026-08-26',
  },
  {
    id: 'sig4',
    docName: 'Supplier NDA - Bidvest Parts.pdf',
    template: 'Mutual NDA',
    signers: [
      { name: 'Bidvest Parts (Pty) Ltd', email: 'legal@bidvestparts.co.za', status: 'signed' },
      { name: 'Naledi Mokoena', email: 'naledi@randauto.co.za', status: 'signed' },
    ],
    status: 'completed',
    createdAt: '2026-08-05T11:00:00',
    dueDate: '2026-08-12',
  },
  {
    id: 'sig5',
    docName: 'Leave Policy Acknowledgement - 2026.pdf',
    template: 'Policy Acknowledgement',
    signers: [{ name: 'R. Dlamini', email: 'r.dlamini@randauto.co.za', status: 'declined' }],
    status: 'declined',
    createdAt: '2026-08-11T09:00:00',
    dueDate: '2026-08-15',
  },
];

export const formTemplates: FormTemplate[] = [
  { id: 'ft1', name: 'FICA Customer Intake', fields: 14, submissions: 212, lastUsed: '2026-08-21', category: 'Vehicle Sales' },
  { id: 'ft2', name: 'New Hire Offer Capture', fields: 22, submissions: 34, lastUsed: '2026-08-19', category: 'HR & Payroll' },
  { id: 'ft3', name: 'Insurance Claim Intake', fields: 18, submissions: 58, lastUsed: '2026-08-14', category: 'Insurance' },
  { id: 'ft4', name: 'Leave Application', fields: 8, submissions: 301, lastUsed: '2026-08-18', category: 'HR & Payroll' },
  { id: 'ft5', name: 'Supplier Onboarding', fields: 16, submissions: 27, lastUsed: '2026-08-09', category: 'Finance' },
];

export const activity: ActivityItem[] = [
  { id: 'a1', actor: 'Johan Pretorius', action: 'approved', target: 'Deal File - VW Polo Vivo - N. Zulu', time: '12 min ago', kind: 'approve' },
  { id: 'a2', actor: 'Scan Queue', action: 'classified & filed', target: 'IMG_20260821_0731.jpg → FICA & RICA', time: '38 min ago', kind: 'scan' },
  { id: 'a3', actor: 'N. Zulu', action: 'signed', target: 'Vehicle Sale Agreement - VW Polo Vivo.pdf', time: '1 hr ago', kind: 'sign' },
  { id: 'a4', actor: 'Riaan de Wet', action: 'uploaded', target: 'Supplier Invoice - Bidvest Parts #88213.pdf', time: '2 hr ago', kind: 'upload' },
  { id: 'a5', actor: 'Thandiwe Nkosi', action: 'started workflow', target: 'New Employee Onboarding — S. Mahlangu', time: '3 hr ago', kind: 'workflow' },
  { id: 'a6', actor: 'Naledi Mokoena', action: 'shared', target: 'Fleet Insurance Renewal 2026.pdf → Nedbank Insurance', time: '5 hr ago', kind: 'share' },
  { id: 'a7', actor: 'R. Dlamini', action: 'declined', target: 'Leave Policy Acknowledgement - 2026.pdf', time: 'Yesterday', kind: 'sign' },
  { id: 'a8', actor: 'System', action: 'archived', target: '14 documents older than 5 years', time: 'Yesterday', kind: 'delete' },
];

export const storageStats = {
  usedGb: 184.6,
  limitGb: 500,
  documentsTotal: 18420,
  documentsThisMonth: 612,
  pagesScannedThisMonth: 2140,
  paperSavedReams: 47,
};

export const monthlyVolume = [
  { month: 'Mar', scanned: 1420, filed: 1380 },
  { month: 'Apr', scanned: 1610, filed: 1590 },
  { month: 'May', scanned: 1780, filed: 1720 },
  { month: 'Jun', scanned: 1930, filed: 1890 },
  { month: 'Jul', scanned: 2040, filed: 2010 },
  { month: 'Aug', scanned: 2140, filed: 2080 },
];

export const departmentBreakdown = [
  { name: 'Vehicle Sales', value: 6120, color: '#D9A441' },
  { name: 'Finance', value: 3840, color: '#1E8E5A' },
  { name: 'HR & Payroll', value: 2910, color: '#2563AC' },
  { name: 'Workshop & Service', value: 3260, color: '#3D4D8F' },
  { name: 'Insurance', value: 2290, color: '#C23B3B' },
];
