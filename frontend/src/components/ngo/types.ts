export interface NGODocument {
  id: number;
  document_type: string;
  file_name: string;
  file_path: string;
  sha256_hash?: string;
  verification_status: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED' | 'REQUEST_CLARIFICATION' | 'PENDING';
  verification_message?: string;
  tamper_risk_score?: number;
  tamper_risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  ocr_text?: string;
  exif_metadata?: string;
  reviewed_by_email?: string;
  review_notes?: string;
  reviewed_at?: string;
  upload_date: string;
}

export interface NGOProfile {
  id: number;
  org_name: string;
  registration_number: string;
  tax_id: string;
  category: string;
  mission_statement: string;
  website: string;
  address: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  doc_completeness_score: number;
  transparency_score: number;
  total_expenses: number;
  total_donations_received: number;
  beneficiary_count: number;
  rejection_reason?: string;
  documents: NGODocument[];
  created_at?: string;
}

export interface Project {
  id: number;
  ngo_id: number;
  project_name: string;
  description?: string;
  category: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  start_date?: string;
  end_date?: string;
  budget?: number;
  total_budget?: number;
  amount_spent?: number;
  total_expenses_claimed?: number;
  fund_utilization_ratio?: number;
  number_of_beneficiaries?: number;
  beneficiary_count?: number;
  target_beneficiaries?: string | number;
  outcomes?: string;
  objective?: string;
  status: 'ACTIVE' | 'COMPLETED' | 'SUSPENDED' | string;
  integrity_status?: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED' | string;
  risk_score?: number;
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  created_at?: string;
  updated_at?: string;
}

export function mapProjectResponse(rawProject: any): Project {
  if (!rawProject) {
    throw new Error("Invalid project data received from API");
  }

  const budgetVal = rawProject.budget !== undefined && rawProject.budget !== null
    ? Number(rawProject.budget)
    : rawProject.total_budget !== undefined && rawProject.total_budget !== null
    ? Number(rawProject.total_budget)
    : undefined;

  const spentVal = rawProject.total_expenses_claimed !== undefined && rawProject.total_expenses_claimed !== null
    ? Number(rawProject.total_expenses_claimed)
    : rawProject.amount_spent !== undefined && rawProject.amount_spent !== null
    ? Number(rawProject.amount_spent)
    : 0;

  const benCount = rawProject.beneficiary_count !== undefined && rawProject.beneficiary_count !== null
    ? Number(rawProject.beneficiary_count)
    : rawProject.number_of_beneficiaries !== undefined && rawProject.number_of_beneficiaries !== null
    ? Number(rawProject.number_of_beneficiaries)
    : 0;

  let utilRatio = rawProject.fund_utilization_ratio;
  if (utilRatio === undefined || utilRatio === null) {
    if (budgetVal && budgetVal > 0) {
      utilRatio = Math.round((spentVal / budgetVal) * 1000) / 10;
    } else {
      utilRatio = 0;
    }
  } else {
    utilRatio = Number(utilRatio);
  }

  return {
    id: rawProject.id,
    ngo_id: rawProject.ngo_id,
    project_name: rawProject.project_name || 'Unnamed Project',
    description: rawProject.description || '',
    category: rawProject.category || 'General',
    location: rawProject.location || undefined,
    latitude: rawProject.latitude !== undefined && rawProject.latitude !== null ? Number(rawProject.latitude) : undefined,
    longitude: rawProject.longitude !== undefined && rawProject.longitude !== null ? Number(rawProject.longitude) : undefined,
    start_date: rawProject.start_date || undefined,
    end_date: rawProject.end_date || undefined,
    budget: budgetVal,
    total_budget: budgetVal,
    total_expenses_claimed: spentVal,
    amount_spent: spentVal,
    beneficiary_count: benCount,
    number_of_beneficiaries: benCount,
    fund_utilization_ratio: utilRatio,
    target_beneficiaries: rawProject.target_beneficiaries,
    outcomes: rawProject.outcomes,
    objective: rawProject.objective,
    status: rawProject.status || 'ACTIVE',
    integrity_status: rawProject.integrity_status || 'VERIFIED',
    risk_score: rawProject.risk_score !== undefined && rawProject.risk_score !== null ? Number(rawProject.risk_score) : 0,
    risk_level: rawProject.risk_level || 'LOW',
    created_at: rawProject.created_at || '',
    updated_at: rawProject.updated_at || undefined,
  };
}

export interface Beneficiary {
  id: number;
  ngo_id: number;
  project_id?: number;
  project_name?: string;
  beneficiary_code: string;
  name_or_alias: string;
  age_group?: string;
  gender?: string;
  location?: string;
  created_at: string;
}

export interface Expense {
  id: number;
  ngo_id: number;
  project_id?: number;
  project_name?: string;
  category: string;
  description?: string;
  amount: number;
  expense_date: string;
  receipt_file_name?: string;
  receipt_file_path?: string;
  receipt_sha256?: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  created_at: string;
}

export interface GovernmentVerification {
  verification_status: 'VERIFIED' | 'PARTIAL_MATCH' | 'FAILED' | 'NOT_VERIFIED';
  verified_at?: string;
  field_matches: {
    registration_number_matched: boolean;
    org_name_matched: boolean;
    tax_id_matched: boolean;
    section_80g_registered: boolean;
    fcra_registered: boolean;
  };
  matched_registry_record?: {
    registry_id: string;
    official_name: string;
    state: string;
    valid_until: string;
  };
  details: string;
}

export interface ProjectEvidence {
  id: number;
  project_id: number;
  ngo_id: number;
  evidence_type: 'BEFORE_PHOTO' | 'DURING_PHOTO' | 'AFTER_PHOTO' | 'CERTIFICATE' | 'INVOICE' | 'RECEIPT' | 'SITE_PHOTO' | 'OTHER_PROOF' | string;
  file_name: string;
  file_path: string;
  sha256_hash?: string;
  p_hash?: string;
  mime_type?: string;
  file_size?: number;
  image_width?: number;
  image_height?: number;
  ocr_text?: string;
  exif_metadata?: string;
  tamper_risk_score: number;
  tamper_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  verification_status: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED';
  evidence_findings?: string;
  upload_timestamp: string;
}

export interface ProjectExpense {
  id: number;
  project_id: number;
  ngo_id: number;
  evidence_id?: number;
  invoice_number?: string;
  vendor_name?: string;
  amount: number;
  ocr_amount?: number;
  is_ocr_matched?: boolean;
  expense_date: string;
  description?: string;
  discrepancy_note?: string;
  created_at?: string;
}

export interface ProjectFinding {
  id: number;
  project_id: number;
  evidence_id?: number;
  category: 'PHOTO_TAMPER' | 'FINANCIAL_FRAUD' | 'DOCUMENT_IDENTITY' | 'EVIDENCE_CONSISTENCY' | string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score_impact: number;
  message: string;
  created_at?: string;
}

export interface ProjectRiskAnalysis {
  id?: number;
  project_id: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED';
  document_identity_risk: number;
  photo_integrity_risk: number;
  financial_integrity_risk: number;
  evidence_consistency_risk: number;
  findings_json?: string;
  recommendation?: string;
}

export interface ProjectDetailData {
  project: Project & {
    integrity_status?: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED';
    risk_score?: number;
    risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  evidence_files: ProjectEvidence[];
  expenses: ProjectExpense[];
  findings: ProjectFinding[];
  risk_analysis?: ProjectRiskAnalysis;
}

export interface ProjectIntegrityAnalysisData {
  project_id: number;
  project_name: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'VERIFIED' | 'NEEDS_ADMIN_REVIEW' | 'REJECTED';
  recommendation?: string;
  category_breakdown: {
    document_identity_risk: number;
    photo_integrity_risk: number;
    financial_integrity_risk: number;
    evidence_consistency_risk: number;
  };
  findings: Array<{
    category: string;
    risk_level: string;
    score_impact: number;
    message: string;
    evidence_id?: number;
  }>;
}
