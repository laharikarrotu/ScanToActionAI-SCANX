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
    let errorMessage = 'Failed to analyze and execute';
    try {
      const error = await response.json();
      errorMessage = error.detail || error.message || errorMessage;
    } catch (e) {
      // If response is not JSON, use status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const result = await response.json();
  
  // Check if result has error status
  if (result.status === 'error') {
    throw new Error(result.message || 'An error occurred while processing');
  }
  
  return result;
}

// Removed analyzeOnly - not used anywhere in the codebase

