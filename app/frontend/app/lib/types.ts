/**
 * TypeScript type definitions for HealthScan frontend
 */

// API Response Types
export interface UISchema {
  page_type: string;
  url_hint?: string | null;
  elements: UIElement[];
}

export interface UIElement {
  id: string;
  type: string;
  label: string;
  value?: string | null;
  position?: { x: number; y: number } | null;
}

export interface ActionStep {
  step: number;
  action: 'fill' | 'click' | 'read' | 'select' | 'navigate' | 'wait';
  target: string;
  value?: string | null;
  description: string;
}

export interface ActionPlan {
  task: string;
  steps: ActionStep[];
  estimated_time?: number;
}

export interface ExecutionLog {
  logs: string[];
  final_url?: string;
  screenshot_path?: string;
}

export interface AnalyzeResponse {
  status: string;
  ui_schema?: UISchema;
  plan?: ActionPlan;
  execution?: ExecutionLog;
  message: string;
  structured_data?: {
    medications?: Medication[];
    prescriber?: string;
    date?: string;
  };
  extracted_data?: Record<string, UIElement>;
}

export interface Medication {
  medication_name: string;
  dosage?: string;
  frequency?: string;
  quantity?: string;
  refills?: string;
  instructions?: string;
}

// Interaction Checker Types
export interface InteractionWarning {
  medication1: string;
  medication2: string;
  description: string;
  recommendation: string;
}

export interface InteractionWarnings {
  major: InteractionWarning[];
  moderate: InteractionWarning[];
  minor: InteractionWarning[];
}

export interface PrescriptionDetail {
  medication_name: string;
  dosage?: string;
  frequency?: string;
  quantity?: string;
  refills?: string;
  instructions?: string;
  prescriber?: string;
  date?: string;
}

export interface InteractionCheckResponse {
  status: string;
  message: string;
  medications_found: number;  // Fixed: Backend returns int, not string
  has_interactions: boolean;
  interactions: InteractionWarnings;
  warnings: InteractionWarnings;  // Alias for interactions (backend compatibility)
  prescriptions?: PrescriptionDetail[];  // Backend primary field name
  prescription_details: PrescriptionDetail[];  // Alias for prescriptions (backend compatibility)
}

// Diet Portal Types
export interface DietRecommendation {
  condition: string;
  foods_to_eat: string[];
  foods_to_avoid: string[];
  nutritional_focus: string;
  warnings?: string[];
}

export interface FoodCompatibility {
  food: string;
  safe: boolean;
  warnings: string[];
  recommendations: string[];
}

export interface MealPlanDay {
  day: number;
  breakfast?: { meal: string };
  lunch?: { meal: string };
  dinner?: { meal: string };
  snacks?: string[];
}

export interface MealPlan {
  meal_plan: MealPlanDay[];
  shopping_list?: string[];
  error?: string;
}

export interface DietRecommendationsResponse {
  status: string;
  message: string;
  recommendations: DietRecommendation;
}

export interface FoodCompatibilityResponse {
  status: string;
  message: string;
  compatibility: FoodCompatibility;
}

export interface MealPlanResponse {
  status: string;
  message: string;
  meal_plan: MealPlan;
}

// Prescription Extraction Types
export interface PrescriptionInfo {
  medication_name: string;
  dosage?: string;
  frequency?: string;
  quantity?: string;
  refills?: string;
  instructions?: string;
  prescriber?: string;
  date?: string;
}

export interface ExtractPrescriptionResponse {
  status: string;
  message: string;
  prescription_info?: PrescriptionInfo;
  cached?: boolean;
}

export interface StreamingProgress {
  step: string;
  progress: number;
  message: string;
  prescription_info?: PrescriptionInfo;
}

export type StreamingCallback = (progress: StreamingProgress) => void;

