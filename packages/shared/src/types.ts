// SYMIONE PAY - Shared Types

// === Enums ===

export type ProofType = 'url' | 'file';

export type AgreementStatus =
  | 'draft'
  | 'awaiting_funding'
  | 'funded'
  | 'proof_submitted'
  | 'validating'
  | 'passed'
  | 'failed'
  | 'manual_review_required'
  | 'paid'
  | 'expired'
  | 'cancelled';

export type PaymentStatus =
  | 'pending'
  | 'authorized'
  | 'captured'
  | 'failed'
  | 'cancelled'
  | 'refunded';

export type SubmissionStatus =
  | 'submitted'
  | 'validating'
  | 'passed'
  | 'failed'
  | 'manual_review_required';

export type DecisionType =
  | 'authorize_payment'
  | 'reject_submission'
  | 'request_manual_review'
  | 'capture_payment';

export type DecisionOutcome =
  | 'approved'
  | 'rejected'
  | 'manual_review'
  | 'error';

export type ReviewStatus = 'open' | 'resolved';

export type ReviewResolution = 'approve' | 'reject';

// === Validation Config Types ===

export interface UrlValidationConfig {
  require_status_200?: boolean;
  allowed_domains?: string[];
  min_lighthouse_score?: number;
  check_mobile_friendly?: boolean;
}

export interface FileValidationConfig {
  allowed_mime_types?: string[];
  max_size_mb?: number;
}

export type ValidationConfig = UrlValidationConfig | FileValidationConfig;

// === Entity Types ===

export interface Agreement {
  id: string;
  public_id: string;
  title: string;
  description: string;
  amount: string; // Decimal as string
  currency: string;
  proof_type: ProofType;
  status: AgreementStatus;
  payer_email: string | null;
  payee_email: string | null;
  funding_url_token: string;
  submit_url_token: string;
  deadline_at: string | null; // ISO date
  created_at: string;
  updated_at: string;
}

export interface AgreementWithConfig extends Agreement {
  validation_config: ValidationConfig;
}

export interface Payment {
  id: string;
  agreement_id: string;
  stripe_payment_intent_id: string | null;
  amount: string;
  currency: string;
  status: PaymentStatus;
  funded_at: string | null;
  captured_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Submission {
  id: string;
  agreement_id: string;
  proof_type: ProofType;
  status: SubmissionStatus;
  url: string | null;
  file_key: string | null;
  file_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  submitted_at: string;
  created_at: string;
}

export interface ValidationResult {
  id: string;
  submission_id: string;
  validator_type: string;
  passed: boolean;
  score: number | null;
  details_json: Record<string, unknown>;
  created_at: string;
}

export interface DecisionLog {
  id: string;
  agreement_id: string;
  submission_id: string | null;
  payment_id: string | null;
  decision_type: DecisionType;
  outcome: DecisionOutcome;
  reason: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface Review {
  id: string;
  agreement_id: string;
  submission_id: string;
  reason: string;
  status: ReviewStatus;
  resolution: ReviewResolution | null;
  resolved_at: string | null;
  created_at: string;
}

export interface FileObject {
  id: string;
  agreement_id: string;
  submission_id: string | null;
  object_key: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  checksum: string | null;
  uploaded_at: string;
  created_at: string;
}

// === API Request/Response Types ===

export interface CreateAgreementRequest {
  title: string;
  description: string;
  amount: number;
  currency?: string;
  proof_type: ProofType;
  validation_config: ValidationConfig;
  payer_email?: string;
  payee_email?: string;
  deadline_at?: string;
}

export interface CreateAgreementResponse {
  agreement: Agreement;
  funding_url: string;
  submit_url: string;
}

export interface PublicAgreementInfo {
  id: string;
  title: string;
  description: string;
  amount: string;
  currency: string;
  proof_type: ProofType;
  status: AgreementStatus;
  deadline_at: string | null;
  validation_rules: string[]; // Human-readable rules
  is_funded: boolean;
  payer_email: string | null;
}

export interface FundAgreementRequest {
  return_url: string;
}

export interface FundAgreementResponse {
  client_secret: string;
  payment_intent_id: string;
}

export interface PresignUploadRequest {
  file_name: string;
  mime_type: string;
  size_bytes: number;
}

export interface PresignUploadResponse {
  upload_url: string;
  object_key: string;
  expires_at: string;
}

export interface CompleteUploadRequest {
  object_key: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
}

export interface SubmitUrlProofRequest {
  url: string;
}

export interface SubmitFileProofRequest {
  file_key: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
}

export interface SubmissionResponse {
  submission: Submission;
  validation_results?: ValidationResult[];
  decision?: DecisionLog;
}

export interface ResolveReviewRequest {
  resolution: ReviewResolution;
  notes?: string;
}

// === Validator Types ===

export interface ValidatorResult {
  passed: boolean;
  score?: number | null;
  reason: string;
  metadata?: Record<string, unknown>;
}
