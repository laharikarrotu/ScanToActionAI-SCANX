/**
 * API client for SCANX backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AnalyzeResponse {
  status: string;
  ui_schema?: any;
  plan?: any;
  execution?: any;
  message: string;
}

export async function analyzeAndExecute(
  imageFile: File,
  intent: string,
  context?: Record<string, any>
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('intent', intent);
  if (context) {
    formData.append('context', JSON.stringify(context));
  }

  const response = await fetch(`${API_BASE_URL}/analyze-and-execute`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to analyze and execute');
  }

  return response.json();
}

export async function analyzeOnly(imageFile: File, hint?: string): Promise<any> {
  const formData = new FormData();
  formData.append('file', imageFile);
  if (hint) {
    formData.append('hint', hint);
  }

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to analyze');
  }

  return response.json();
}

