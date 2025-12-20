'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Types
export interface Medication {
  medication_name: string;
  dosage?: string;
  frequency?: string;
  quantity?: string;
  refills?: string;
  instructions?: string;
}

export interface PrescriptionData {
  medications: Medication[];
  prescriber?: string;
  date?: string;
  imagePreview?: string;
}

import type { InteractionWarnings, PrescriptionDetail } from '../lib/types';

export interface InteractionResult {
  warnings: InteractionWarnings;
  prescription_details: PrescriptionDetail[];
}

export interface DietData {
  condition: string;
  medications: string;
  dietary_restrictions?: string;
}

interface HealthScanState {
  // Prescription data
  prescriptionData: PrescriptionData | null;
  setPrescriptionData: (data: PrescriptionData | null) => void;
  
  // Interaction results
  interactionResult: InteractionResult | null;
  setInteractionResult: (result: InteractionResult | null) => void;
  
  // Diet data
  dietData: DietData | null;
  setDietData: (data: DietData | null) => void;
  
  // Progress tracking
  currentStep: 'scan' | 'interactions' | 'diet' | null;
  setCurrentStep: (step: 'scan' | 'interactions' | 'diet' | null) => void;
  
  // Error state
  errors: Record<string, string | null>;
  setError: (key: string, error: string | null) => void;
  clearErrors: () => void;
  
  // Validation
  validateStep: (step: 'scan' | 'interactions' | 'diet') => { valid: boolean; message?: string };
  
  // Navigation helpers
  navigateToInteractions: () => void;
  navigateToDiet: () => void;
  resetAll: () => void;
}

const HealthScanContext = createContext<HealthScanState | undefined>(undefined);

export function HealthScanProvider({ children }: { children: ReactNode }) {
  const [prescriptionData, setPrescriptionData] = useState<PrescriptionData | null>(null);
  const [interactionResult, setInteractionResult] = useState<InteractionResult | null>(null);
  const [dietData, setDietData] = useState<DietData | null>(null);
  const [currentStep, setCurrentStep] = useState<'scan' | 'interactions' | 'diet' | null>(null);
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const setError = useCallback((key: string, error: string | null) => {
    setErrors(prev => ({ ...prev, [key]: error }));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  const validateStep = useCallback((step: 'scan' | 'interactions' | 'diet'): { valid: boolean; message?: string } => {
    switch (step) {
      case 'scan':
        if (!prescriptionData || !prescriptionData.medications || prescriptionData.medications.length === 0) {
          return { valid: false, message: 'Please scan a prescription first' };
        }
        return { valid: true };
      
      case 'interactions':
        if (!prescriptionData || !prescriptionData.medications || prescriptionData.medications.length === 0) {
          return { valid: false, message: 'No prescription data available. Please scan a prescription first.' };
        }
        return { valid: true };
      
      case 'diet':
        if (!dietData || !dietData.condition) {
          return { valid: false, message: 'Please enter a medical condition' };
        }
        // Auto-populate medications from prescription if available
        if (!dietData.medications && prescriptionData) {
          const medNames = prescriptionData.medications.map(m => m.medication_name).join(', ');
          setDietData(prev => ({ ...prev, medications: medNames } as DietData));
        }
        return { valid: true };
      
      default:
        return { valid: false, message: 'Invalid step' };
    }
  }, [prescriptionData, dietData]);

  const navigateToInteractions = useCallback(() => {
    const validation = validateStep('scan');
    if (!validation.valid) {
      setError('navigation', validation.message || 'Cannot navigate to interactions');
      return false;
    }
    setCurrentStep('interactions');
    clearErrors();
    return true;
  }, [validateStep, setError, clearErrors]);

  const navigateToDiet = useCallback(() => {
    // Can navigate from either scan or interactions
    if (prescriptionData && prescriptionData.medications.length > 0) {
      // Auto-populate medications
      const medNames = prescriptionData.medications.map(m => m.medication_name).join(', ');
      setDietData(prev => ({
        condition: prev?.condition || '',
        medications: medNames,
        dietary_restrictions: prev?.dietary_restrictions || ''
      }));
    }
    setCurrentStep('diet');
    clearErrors();
    return true;
  }, [prescriptionData, setDietData, clearErrors]);

  const resetAll = useCallback(() => {
    setPrescriptionData(null);
    setInteractionResult(null);
    setDietData(null);
    setCurrentStep(null);
    clearErrors();
  }, [clearErrors]);

  const value: HealthScanState = {
    prescriptionData,
    setPrescriptionData,
    interactionResult,
    setInteractionResult,
    dietData,
    setDietData,
    currentStep,
    setCurrentStep,
    errors,
    setError,
    clearErrors,
    validateStep,
    navigateToInteractions,
    navigateToDiet,
    resetAll,
  };

  return (
    <HealthScanContext.Provider value={value}>
      {children}
    </HealthScanContext.Provider>
  );
}

export function useHealthScan() {
  const context = useContext(HealthScanContext);
  if (context === undefined) {
    throw new Error('useHealthScan must be used within a HealthScanProvider');
  }
  return context;
}

