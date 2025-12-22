'use client';

import { useState, useEffect } from 'react';
import type { DietRecommendation, FoodCompatibility, MealPlan, MealPlanDay } from '../lib/types';
import ProgressTracker from './ProgressTracker';
import { useHealthScan } from '../context/HealthScanContext';
import { API_BASE_URL } from '../lib/api';
import { safeStorage } from '../lib/storage';
import MedicalDisclaimer from './MedicalDisclaimer';

export default function DietPortal() {
  const {
    prescriptionData,
    dietData,
    setDietData,
    setCurrentStep,
    errors,
    setError,
    clearErrors,
    validateStep,
  } = useHealthScan();
  
  const [condition, setCondition] = useState(dietData?.condition || '');
  const [medications, setMedications] = useState(dietData?.medications || '');
  const [dietaryRestrictions, setDietaryRestrictions] = useState(dietData?.dietary_restrictions || '');
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<DietRecommendation | null>(null);
  const [foodCheckResult, setFoodCheckResult] = useState<FoodCompatibility | null>(null);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [mealPlanDays, setMealPlanDays] = useState(7);
  const [foodItem, setFoodItem] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'food-check' | 'meal-plan' | 'chat'>('recommendations');
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [chatLoading, setChatLoading] = useState(false);
  
  // Set current step on mount
  useEffect(() => {
    setCurrentStep('diet');
  }, [setCurrentStep]);
  
  // Auto-populate from context
  useEffect(() => {
    if (prescriptionData && prescriptionData.medications.length > 0 && !medications) {
      const medNames = prescriptionData.medications.map(m => m.medication_name).join(', ');
      setMedications(medNames);
      setDietData({
        condition: condition || '',
        medications: medNames,
        dietary_restrictions: dietaryRestrictions || '',
      });
    }
  }, [prescriptionData, medications, condition, dietaryRestrictions, setDietData]);
  
  // Update context when form changes
  useEffect(() => {
    setDietData({
      condition,
      medications,
      dietary_restrictions: dietaryRestrictions,
    });
  }, [condition, medications, dietaryRestrictions, setDietData]);

  const handleGetRecommendations = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate step
    const validation = validateStep('diet');
    if (!validation.valid) {
      setLocalError(validation.message || 'Please enter a medical condition');
      setError('diet', validation.message || 'Please enter a medical condition');
      return;
    }

    setLoading(true);
    setLocalError(null);
    clearErrors();

    try {
      const formData = new FormData();
      formData.append('condition', condition);
      if (medications.trim()) formData.append('medications', medications);
      if (dietaryRestrictions.trim()) formData.append('dietary_restrictions', dietaryRestrictions);

      const response = await fetch(`${API_BASE_URL}/get-diet-recommendations`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to get recommendations';
        try {
        const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      if (data.status === 'error') {
        throw new Error(data.message || 'An error occurred while getting recommendations');
      }
      
      if (!data.recommendations) {
        throw new Error('Invalid response format from server');
      }
      
      setRecommendations(data.recommendations);
      clearErrors();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong';
      setLocalError(errorMsg);
      setError('diet', errorMsg);
      
      // Error recovery
      if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        setError('diet', 'Network error. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCheckFood = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!foodItem.trim()) {
      setLocalError('Please enter a food item');
      setError('diet', 'Please enter a food item');
      return;
    }

    setLoading(true);
    setLocalError(null);
    clearErrors();

    try {
      const formData = new FormData();
      formData.append('food_item', foodItem);
      if (condition.trim()) formData.append('condition', condition);
      if (medications.trim()) formData.append('medications', medications);

      const response = await fetch(`${API_BASE_URL}/check-food-compatibility`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to check food';
        try {
        const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      if (data.status === 'error') {
        throw new Error(data.message || 'An error occurred while checking food compatibility');
      }
      
      if (!data.compatibility) {
        throw new Error('Invalid response format from server');
      }
      
      setFoodCheckResult(data.compatibility);
      clearErrors();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong';
      setLocalError(errorMsg);
      setError('diet', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMealPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!condition.trim()) {
      setLocalError('Please enter a medical condition');
      setError('diet', 'Please enter a medical condition');
      return;
    }

    setLoading(true);
    setLocalError(null);
    clearErrors();

    try {
      const formData = new FormData();
      formData.append('condition', condition);
      formData.append('days', mealPlanDays.toString());
      if (dietaryRestrictions.trim()) formData.append('dietary_restrictions', dietaryRestrictions);

      const response = await fetch(`${API_BASE_URL}/generate-meal-plan`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to generate meal plan';
        try {
        const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      if (data.status === 'error') {
        throw new Error(data.message || 'An error occurred while generating meal plan');
      }
      
      if (!data.meal_plan) {
        throw new Error('Invalid response format from server');
      }
      
      setMealPlan(data.meal_plan);
      clearErrors();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong';
      setLocalError(errorMsg);
      setError('diet', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full w-full text-slate-800 relative overflow-y-auto">
      {/* Medical Background - Consistent with other pages */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(2,132,199,0.05),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(6,182,212,0.05),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(5,150,105,0.03),transparent_50%)]"></div>
      </div>

      <div className="relative w-full mx-auto px-6 md:px-10 py-4 md:py-6 z-10">
        <div className="mb-6 md:mb-8 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 mb-4 shadow-lg glow-teal medical-card">
            <span className="text-2xl sm:text-3xl">🥗</span>
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 gradient-text">Diet & Nutrition Portal</h1>
          <p className="text-sm sm:text-base text-slate-600 font-medium px-2">Personalized diet recommendations based on your medical condition</p>
        </div>

        {/* Tabs - Medical Theme - Responsive */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-2 mb-6 glass-strong p-2 rounded-xl border border-blue-200/50">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg font-semibold text-xs sm:text-sm transition-all min-h-[44px] ${
              activeTab === 'recommendations' 
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg glow' 
                : 'text-slate-700 hover:bg-blue-50 border border-transparent hover:border-blue-200'
            }`}
            aria-label="Diet recommendations tab"
          >
            Recommendations
          </button>
          <button
            onClick={() => setActiveTab('food-check')}
            className={`flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg font-semibold text-xs sm:text-sm transition-all min-h-[44px] ${
              activeTab === 'food-check' 
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg glow' 
                : 'text-slate-700 hover:bg-blue-50 border border-transparent hover:border-blue-200'
            }`}
            aria-label="Food compatibility check tab"
          >
            Check Food
          </button>
          <button
            onClick={() => setActiveTab('meal-plan')}
            className={`flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg font-semibold text-xs sm:text-sm transition-all min-h-[44px] ${
              activeTab === 'meal-plan' 
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg glow' 
                : 'text-slate-700 hover:bg-blue-50 border border-transparent hover:border-blue-200'
            }`}
            aria-label="Meal plan generator tab"
          >
            Meal Plan
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg font-semibold text-xs sm:text-sm transition-all min-h-[44px] ${
              activeTab === 'chat' 
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg glow' 
                : 'text-slate-700 hover:bg-blue-50 border border-transparent hover:border-blue-200'
            }`}
            aria-label="Ask questions tab"
          >
            💬 Ask Questions
          </button>
        </div>

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            <form onSubmit={handleGetRecommendations} className="medical-card p-4 sm:p-6" aria-label="Diet recommendations form">
              <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">Get Diet Recommendations</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Medical Condition/Diagnosis *</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Type 2 Diabetes, Hypertension, Kidney Disease"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    required
                    aria-label="Enter medical condition or diagnosis"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Current Medications (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    placeholder="e.g., Metformin, Warfarin, Lisinopril"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    aria-label="Enter current medications"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Dietary Restrictions (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={dietaryRestrictions}
                    onChange={(e) => setDietaryRestrictions(e.target.value)}
                    placeholder="e.g., Vegetarian, Gluten-free, Dairy-free"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    aria-label="Enter dietary restrictions"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary text-white font-semibold py-3 sm:py-4 px-6 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all min-h-[44px]"
                  aria-label={loading ? "Getting recommendations" : "Get diet recommendations"}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="spinner w-4 h-4 border-2 border-white border-t-transparent"></div>
                      Getting Recommendations...
                    </span>
                  ) : (
                    'Get Recommendations'
                  )}
                </button>
              </div>
            </form>

            {recommendations && (
              <div className="medical-card p-4 sm:p-6 space-y-4 animate-in fade-in">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-800 mb-2">Diet Recommendations for {recommendations.condition}</h2>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="medical-card bg-blue-50 border-2 border-blue-300 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">✅</span>
                      <h3 className="font-bold text-blue-700 text-lg">Foods to Eat</h3>
                    </div>
                    <ul className="list-disc list-inside space-y-2 text-sm text-slate-700">
                      {recommendations.foods_to_eat.map((food: string, idx: number) => (
                        <li key={idx} className="pl-2">{food}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="medical-card bg-red-50 border-2 border-red-300 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">❌</span>
                      <h3 className="font-bold text-red-700 text-lg">Foods to Avoid</h3>
                    </div>
                    <ul className="list-disc list-inside space-y-2 text-sm text-slate-700">
                      {recommendations.foods_to_avoid.map((food: string, idx: number) => (
                        <li key={idx} className="pl-2">{food}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                <div className="medical-card bg-blue-50 border-2 border-blue-300 rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">🎯</span>
                    <h3 className="font-bold text-blue-700 text-lg">Nutritional Focus</h3>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{recommendations.nutritional_focus}</p>
                </div>
                
                {recommendations.warnings && recommendations.warnings.length > 0 && (
                  <div className="medical-card bg-amber-50 border-2 border-amber-300 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">⚠️</span>
                      <h3 className="font-bold text-amber-700 text-lg">Important Warnings</h3>
                    </div>
                    <ul className="list-disc list-inside space-y-2 text-sm text-slate-700">
                      {recommendations.warnings.map((warning: string, idx: number) => (
                        <li key={idx} className="pl-2">{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Food Check Tab */}
        {activeTab === 'food-check' && (
          <div className="space-y-6">
            <form onSubmit={handleCheckFood} className="medical-card p-6" aria-label="Food compatibility check form">
              <h2 className="text-xl font-semibold mb-4 text-slate-800">Check Food Compatibility</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Food Item *</label>
                  <input
                    type="text"
                    value={foodItem}
                    onChange={(e) => setFoodItem(e.target.value)}
                    placeholder="e.g., Grapefruit, Spinach, Aged Cheese"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    required
                    aria-label="Enter food item to check"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Medical Condition (optional)</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Diabetes, Hypertension"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    aria-label="Enter medical condition"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Medications (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    placeholder="e.g., Warfarin, Metformin"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    aria-label="Enter medications"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary text-white font-semibold py-3 sm:py-4 px-6 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all min-h-[44px]"
                  aria-label={loading ? "Checking food compatibility" : "Check food compatibility"}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="spinner w-4 h-4 border-2 border-white border-t-transparent"></div>
                      Checking...
                    </span>
                  ) : (
                    'Check Food'
                  )}
                </button>
              </div>
            </form>

            {foodCheckResult && (
              <div className="medical-card p-4 sm:p-6 animate-in fade-in">
                <h2 className="text-xl sm:text-2xl font-bold mb-4 text-slate-800">Compatibility Check: {foodCheckResult.food}</h2>
                
                {foodCheckResult.safe ? (
                  <div className="medical-card bg-blue-50 border-2 border-blue-300 rounded-xl p-5 mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">✅</span>
                      <p className="text-blue-700 font-bold text-lg">Generally Safe</p>
                    </div>
                  </div>
                ) : (
                  <div className="medical-card bg-red-50 border-2 border-red-300 rounded-xl p-5 mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">⚠️</span>
                      <p className="text-red-700 font-bold text-lg">Potential Issues</p>
                    </div>
                  </div>
                )}
                
                {foodCheckResult.warnings.length > 0 && (
                  <div className="mt-4 space-y-3">
                    {foodCheckResult.warnings.map((warning: string, idx: number) => (
                      <div key={idx} className="medical-card bg-amber-50 border-2 border-amber-300 rounded-xl p-4">
                        <p className="text-sm text-slate-700">{warning}</p>
                      </div>
                    ))}
                  </div>
                )}
                
                {foodCheckResult.recommendations.length > 0 && (
                  <div className="mt-4 medical-card bg-blue-50 border-2 border-blue-300 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xl">💡</span>
                      <h3 className="font-bold text-blue-700">Recommendations</h3>
                    </div>
                    {foodCheckResult.recommendations.map((rec: string, idx: number) => (
                      <p key={idx} className="text-sm text-slate-700 mb-2 pl-6">{rec}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Meal Plan Tab */}
        {activeTab === 'meal-plan' && (
          <div className="space-y-6">
            <form onSubmit={handleGenerateMealPlan} className="medical-card p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">Generate Meal Plan</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Medical Condition *</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Type 2 Diabetes, Hypertension"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Number of Days</label>
                  <input
                    type="number"
                    value={mealPlanDays}
                    onChange={(e) => setMealPlanDays(parseInt(e.target.value))}
                    min="1"
                    max="14"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold mb-2 text-slate-700">Dietary Restrictions (optional)</label>
                  <input
                    type="text"
                    value={dietaryRestrictions}
                    onChange={(e) => setDietaryRestrictions(e.target.value)}
                    placeholder="e.g., Vegetarian, Gluten-free"
                    className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base sm:text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary text-white font-semibold py-3 sm:py-4 px-6 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all min-h-[44px]"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="spinner w-4 h-4 border-2 border-white border-t-transparent"></div>
                      Generating Meal Plan...
                    </span>
                  ) : (
                    'Generate Meal Plan'
                  )}
                </button>
              </div>
            </form>

            {mealPlan && !mealPlan.error && (
              <div className="medical-card p-4 sm:p-6 space-y-4">
                <h2 className="text-lg sm:text-xl font-semibold text-slate-800">{mealPlanDays}-Day Meal Plan for {condition}</h2>
                
                {mealPlan.meal_plan && mealPlan.meal_plan.map((day: MealPlanDay, idx: number) => (
                  <div key={idx} className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                    <h3 className="font-semibold mb-2 text-slate-800">Day {day.day}</h3>
                    <div className="space-y-2 text-sm text-slate-700">
                      <p><strong>Breakfast:</strong> {day.breakfast?.meal}</p>
                      <p><strong>Lunch:</strong> {day.lunch?.meal}</p>
                      <p><strong>Dinner:</strong> {day.dinner?.meal}</p>
                      <p><strong>Snacks:</strong> {day.snacks?.join(', ')}</p>
                    </div>
                  </div>
                ))}
                
                {mealPlan.shopping_list && (
                  <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                    <h3 className="font-semibold text-blue-700 mb-2">🛒 Shopping List</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
                      {mealPlan.shopping_list.map((item: string, idx: number) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="space-y-6">
            <div className="medical-card p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">💬 Ask Me Anything About Your Diet</h2>
              <p className="text-slate-600 mb-4 text-sm">
                I can answer questions about your diet recommendations, food compatibility, meal plans, and more.
                {condition && ` I see you're managing: ${condition}`}
                {medications && ` with medications: ${medications}`}
              </p>

              {/* Chat Messages */}
              <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4 mb-4 h-64 overflow-y-auto space-y-3">
                {chatMessages.length === 0 && (
                  <div className="text-slate-600 text-sm text-center py-8">
                    Ask me anything! For example:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>"What foods should I avoid with my medications?"</li>
                      <li>"Can I eat grapefruit with my current medications?"</li>
                      <li>"What's a good breakfast for my condition?"</li>
                    </ul>
                  </div>
                )}
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-xl p-3 ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                          : 'medical-card bg-white text-slate-800 border-blue-200'
                      }`}
                    >
                      <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="medical-card bg-white rounded-xl p-3">
                      <div className="flex gap-1">
                        <span className="animate-bounce text-blue-600">●</span>
                        <span className="animate-bounce delay-75 text-blue-600">●</span>
                        <span className="animate-bounce delay-150 text-blue-600">●</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!chatInput.trim() || chatLoading) return;

                  const userMessage = chatInput.trim();
                  setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
                  setChatInput('');
                  setChatLoading(true);

                  try {
                    const response = await fetch(`${API_BASE_URL}/chat`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        message: userMessage,
                        context: {
                          prescription_data: prescriptionData,
                          interaction_result: null,
                          diet_data: {
                            condition,
                            medications,
                            dietary_restrictions: dietaryRestrictions,
                          },
                        },
                      }),
                    });

                    if (!response.ok) {
                      let errorMessage = 'Failed to get a response from the AI';
                      try {
                        const error = await response.json();
                        errorMessage = error.detail || error.message || errorMessage;
                      } catch (e) {
                        errorMessage = response.statusText || errorMessage;
                      }
                      throw new Error(errorMessage);
                    }

                      const data = await response.json();
                    if (data.status === 'error') {
                      throw new Error(data.message || 'An error occurred');
                    }
                    
                    const responseText = data.response || data.message || 'I understand your question. Let me help you with that.';
                      setChatMessages(prev => [
                        ...prev,
                      { role: 'assistant', content: responseText }
                    ]);
                  } catch (err: unknown) {
                    const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred';
                    let errorMessage = `Sorry, I encountered an error: ${errorMsg}.`;
                    if (errorMsg.includes('Failed to fetch') || errorMsg.includes('Network')) {
                      errorMessage = 'Network error. Please check your connection and try again.';
                    }
                    setChatMessages(prev => [
                      ...prev,
                      { role: 'assistant', content: errorMessage }
                    ]);
                  } finally {
                    setChatLoading(false);
                  }
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask me anything about your diet..."
                  className="flex-1 medical-card border border-blue-200 rounded-xl px-4 py-2 text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
                  disabled={chatLoading}
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="px-6 py-2 btn-primary disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold transition-all min-h-[44px]"
                >
                  Send
                </button>
              </form>
            </div>
          </div>
        )}

        {(localError || errors.diet) && (
          <div className="medical-card bg-red-50 border-2 border-red-200 rounded-xl p-4 mt-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <p className="text-red-800 font-semibold mb-1">Error</p>
                <p className="text-red-700 text-sm">{localError || errors.diet}</p>
            {(localError || errors.diet)?.includes('Network') && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  if (activeTab === 'recommendations') handleGetRecommendations(e);
                }}
                    className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                    aria-label="Retry request"
              >
                🔄 Retry
              </button>
            )}
              </div>
            </div>
          </div>
        )}

        {/* Medical Disclaimer */}
        <MedicalDisclaimer className="mt-6" />
      </div>

      {/* Footer Medical Disclaimer */}
      <MedicalDisclaimer variant="footer" className="mt-12" />
    </div>
  );
}
