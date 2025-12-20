/**
 * Image Quality Checker for Mobile
 * Provides real-time feedback on image quality before upload
 */
import * as FileSystem from 'expo-file-system';

export interface QualityCheckResult {
  isValid: boolean;
  issues: string[];
  warnings: string[];
  score: number; // 0-100
  recommendations: string[];
}

export async function checkImageQuality(imageUri: string): Promise<QualityCheckResult> {
  /**
   * Check image quality and provide feedback.
   * 
   * Note: Full image analysis requires backend API call.
   * This is a lightweight client-side check.
   */
  const issues: string[] = [];
  const warnings: string[] = [];
  const recommendations: string[] = [];
  let score = 100;

  try {
    // Check file size
    const fileInfo = await FileSystem.getInfoAsync(imageUri);
    if (fileInfo.exists && 'size' in fileInfo) {
      const sizeMB = fileInfo.size / (1024 * 1024);
      if (sizeMB > 10) {
        issues.push('Image is too large (>10MB)');
        score -= 30;
        recommendations.push('Compress the image or use a smaller file');
      } else if (sizeMB < 0.01) {
        warnings.push('Image is very small (<10KB) - may be low quality');
        score -= 10;
        recommendations.push('Use a higher quality image');
      }
    }

    // Basic checks (we can't do full blur/lighting analysis on client)
    // These would require image processing libraries or backend API call
    
    // For now, provide general recommendations
    if (score < 70) {
      recommendations.push('Try taking the photo again with better lighting');
      recommendations.push('Ensure the document is flat and in focus');
      recommendations.push('Avoid shadows and glare');
    }

    return {
      isValid: issues.length === 0,
      issues,
      warnings,
      score: Math.max(0, score),
      recommendations
    };
  } catch (error) {
    return {
      isValid: false,
      issues: ['Could not check image quality'],
      warnings: [],
      score: 0,
      recommendations: ['Please try selecting the image again']
    };
  }
}

export async function checkImageQualityWithBackend(
  imageUri: string,
  apiBaseUrl: string
): Promise<QualityCheckResult> {
  /**
   * Check image quality using backend API for accurate analysis.
   * This provides blur, lighting, and resolution checks.
   */
  try {
    const FormData = require('form-data');
    const formData = new FormData();
    
    formData.append('file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'photo.jpg',
    } as any);

    const response = await fetch(`${apiBaseUrl}/check-image-quality`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (!response.ok) {
      throw new Error('Quality check failed');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    // Fallback to client-side check
    return checkImageQuality(imageUri);
  }
}

