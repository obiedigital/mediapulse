export type Role = 'Admin' | 'Manager' | 'Staff';

export interface DemoUser {
  id: string;
  name: string;
  role: Role;
  department: string;
  org: string;
  email: string;
  initials: string;
  color: string;
}

export interface FolderNode {
  id: string;
  name: string;
  parentId: string | null;
  docCount: number;
}

export type DocType = 'pdf' | 'image' | 'doc' | 'xlsx' | 'email';
export type DocStatus = 'active' | 'pending-review' | 'archived';

export interface DocumentItem {
  id: string;
  name: string;
  folderId: string;
  type: DocType;
  sizeKb: number;
  owner: string;
  updatedAt: string;
  tags: string[];
  status: DocStatus;
  starred?: boolean;
  compliance?: 'POPIA' | 'FICA' | 'FSCA' | null;
}

export type ScanStatus = 'queued' | 'processing' | 'classified' | 'filed';

export interface ScanJob {
  id: string;
  fileName: string;
  source: 'Mobile App' | 'Network Scanner' | 'Email Import' | 'Bulk Upload';
  pages: number;
  status: ScanStatus;
  destinationFolder: string;
  confidence: number;
  submittedBy: string;
  submittedAt: string;
}

export type WorkflowStepType = 'approval' | 'condition' | 'notification' | 'form';

export interface WorkflowStep {
  id: string;
  name: string;
  type: WorkflowStepType;
  assignee?: string;
  detail: string;
}

export interface WorkflowDef {
  id: string;
  name: string;
  description: string;
  category: string;
  steps: WorkflowStep[];
  activeInstances: number;
  completedThisMonth: number;
  avgCompletionHrs: number;
  color: string;
}

export type InstanceStatus = 'in-progress' | 'approved' | 'rejected' | 'waiting';

export interface WorkflowInstance {
  id: string;
  workflowId: string;
  documentName: string;
  currentStepIndex: number;
  status: InstanceStatus;
  startedAt: string;
  requester: string;
  waitingOn?: string;
}

export type SignerStatus = 'pending' | 'viewed' | 'signed' | 'declined';

export interface Signer {
  name: string;
  email: string;
  status: SignerStatus;
}

export type SignatureStatus = 'draft' | 'sent' | 'partially-signed' | 'completed' | 'declined' | 'expired';

export interface SignatureRequest {
  id: string;
  docName: string;
  template: string;
  signers: Signer[];
  status: SignatureStatus;
  createdAt: string;
  dueDate: string;
}

export interface FormTemplate {
  id: string;
  name: string;
  fields: number;
  submissions: number;
  lastUsed: string;
  category: string;
}

export interface ActivityItem {
  id: string;
  actor: string;
  action: string;
  target: string;
  time: string;
  kind: 'upload' | 'scan' | 'approve' | 'sign' | 'workflow' | 'share' | 'delete';
}
