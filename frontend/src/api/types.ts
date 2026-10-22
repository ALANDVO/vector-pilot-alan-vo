export interface EvaluationBase {
  name: string;
  description?: string;
  dataset_name: string;
  dataset_version: string;
  config?: Record<string, unknown>;
}

export interface EvaluationCreate extends EvaluationBase {}

export interface EvaluationUpdate {
  name?: string;
  description?: string;
  dataset_name?: string;
  dataset_version?: string;
  config?: Record<string, unknown>;
  status?: string;
}

export interface EvaluationRead {
  id: number;
  name: string;
  description?: string;
  dataset_name: string;
  dataset_version: string;
  status: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  config?: string;
}

export interface EvaluationListResponse {
  items: EvaluationRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface EvaluationRunBase {
  model_provider: string;
  model_name: string;
  model_config_json?: Record<string, unknown>;
}

export interface EvaluationRunCreate extends EvaluationRunBase {}

export interface EvaluationRunRead {
  id: number;
  evaluation_id: number;
  model_provider: string;
  model_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  model_config_json?: string;
}

export interface EvaluationMetricBase {
  name: string;
  value: number;
  details?: Record<string, unknown>;
}

export interface EvaluationMetricRead {
  id: number;
  run_id: number;
  name: string;
  value: number;
  details?: string;
}

export interface EvaluationWithRuns extends EvaluationRead {
  runs: EvaluationRunRead[];
}

export interface EvaluationRunWithMetrics extends EvaluationRunRead {
  metrics: EvaluationMetricRead[];
}