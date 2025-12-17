/**
 * API client for SCANX mobile app
 */
import axios from 'axios';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export interface AnalyzeResponse {
  status: string;
  ui_schema?: any;
  plan?: any;
  execution?: any;
  message: string;
}

export async function analyzeAndExecute(
  imageUri: string,
  intent: string,
  context?: Record<string, any>
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  
  // React Native FormData format
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'photo.jpg',
  } as any);
  
  formData.append('intent', intent);
  if (context) {
    formData.append('context', JSON.stringify(context));
  }

  const response = await axios.post(`${API_BASE_URL}/analyze-and-execute`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

export async function analyzeOnly(imageUri: string, hint?: string): Promise<any> {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'photo.jpg',
  } as any);
  if (hint) {
    formData.append('hint', hint);
  }

  const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

