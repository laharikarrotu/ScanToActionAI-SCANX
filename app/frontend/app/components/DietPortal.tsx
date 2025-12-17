'use client';

import { useState } from 'react';

export default function DietPortal() {
  const [condition, setCondition] = useState('');
  const [medications, setMedications] = useState('');
  const [dietaryRestrictions, setDietaryRestrictions] = useState('');
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'food-check' | 'meal-plan'>('recommendations');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleGetRecommendations = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!condition.trim()) {
      setError('Please enter a medical condition');
      return;
    }

    setLoading(true);
    setError(null);

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
        const error = await response.json();
        throw new Error(error.message || 'Failed to get recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const [foodItem, setFoodItem] = useState('');
  const [foodCheckResult, setFoodCheckResult] = useState<any>(null);

  const handleCheckFood = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!foodItem.trim()) {
      setError('Please enter a food item');
      return;
    }

    setLoading(true);
    setError(null);

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
        const error = await response.json();
        throw new Error(error.message || 'Failed to check food');
      }

      const data = await response.json();
      setFoodCheckResult(data.compatibility);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const [mealPlanDays, setMealPlanDays] = useState(7);
  const [mealPlan, setMealPlan] = useState<any>(null);

  const handleGenerateMealPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!condition.trim()) {
      setError('Please enter a medical condition');
      return;
    }

    setLoading(true);
    setError(null);

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
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate meal plan');
      }

      const data = await response.json();
      setMealPlan(data.meal_plan);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-green-950 text-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">🥗 Diet & Nutrition Portal</h1>
          <p className="text-green-300">Personalized diet recommendations based on your medical condition</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-zinc-800 p-2 rounded-lg">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`flex-1 px-4 py-2 rounded ${activeTab === 'recommendations' ? 'bg-green-600' : 'bg-zinc-700'}`}
          >
            Recommendations
          </button>
          <button
            onClick={() => setActiveTab('food-check')}
            className={`flex-1 px-4 py-2 rounded ${activeTab === 'food-check' ? 'bg-green-600' : 'bg-zinc-700'}`}
          >
            Check Food
          </button>
          <button
            onClick={() => setActiveTab('meal-plan')}
            className={`flex-1 px-4 py-2 rounded ${activeTab === 'meal-plan' ? 'bg-green-600' : 'bg-zinc-700'}`}
          >
            Meal Plan
          </button>
        </div>

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            <form onSubmit={handleGetRecommendations} className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
              <h2 className="text-xl font-semibold mb-4">Get Diet Recommendations</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2">Medical Condition/Diagnosis *</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Type 2 Diabetes, Hypertension, Kidney Disease"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Current Medications (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    placeholder="e.g., Metformin, Warfarin, Lisinopril"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Dietary Restrictions (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={dietaryRestrictions}
                    onChange={(e) => setDietaryRestrictions(e.target.value)}
                    placeholder="e.g., Vegetarian, Gluten-free, Dairy-free"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-zinc-700 text-white font-semibold py-3 px-6 rounded-lg"
                >
                  {loading ? 'Getting Recommendations...' : 'Get Recommendations'}
                </button>
              </div>
            </form>

            {recommendations && (
              <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700 space-y-4">
                <h2 className="text-xl font-semibold">Diet Recommendations for {recommendations.condition}</h2>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                    <h3 className="font-semibold text-green-400 mb-2">✅ Foods to Eat</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {recommendations.foods_to_eat.map((food: string, idx: number) => (
                        <li key={idx}>{food}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <h3 className="font-semibold text-red-400 mb-2">❌ Foods to Avoid</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {recommendations.foods_to_avoid.map((food: string, idx: number) => (
                        <li key={idx}>{food}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-400 mb-2">🎯 Nutritional Focus</h3>
                  <p className="text-sm">{recommendations.nutritional_focus}</p>
                </div>
                
                {recommendations.warnings && recommendations.warnings.length > 0 && (
                  <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
                    <h3 className="font-semibold text-yellow-400 mb-2">⚠️ Important Warnings</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {recommendations.warnings.map((warning: string, idx: number) => (
                        <li key={idx}>{warning}</li>
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
            <form onSubmit={handleCheckFood} className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
              <h2 className="text-xl font-semibold mb-4">Check Food Compatibility</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2">Food Item *</label>
                  <input
                    type="text"
                    value={foodItem}
                    onChange={(e) => setFoodItem(e.target.value)}
                    placeholder="e.g., Grapefruit, Spinach, Aged Cheese"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Medical Condition (optional)</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Diabetes, Hypertension"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Medications (optional, comma-separated)</label>
                  <input
                    type="text"
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    placeholder="e.g., Warfarin, Metformin"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-zinc-700 text-white font-semibold py-3 px-6 rounded-lg"
                >
                  {loading ? 'Checking...' : 'Check Food'}
                </button>
              </div>
            </form>

            {foodCheckResult && (
              <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
                <h2 className="text-xl font-semibold mb-4">Compatibility Check: {foodCheckResult.food}</h2>
                
                {foodCheckResult.safe ? (
                  <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                    <p className="text-green-400 font-semibold">✅ Generally Safe</p>
                  </div>
                ) : (
                  <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400 font-semibold">⚠️ Potential Issues</p>
                  </div>
                )}
                
                {foodCheckResult.warnings.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {foodCheckResult.warnings.map((warning: string, idx: number) => (
                      <div key={idx} className="bg-yellow-900/30 border border-yellow-700 rounded p-3 text-sm">
                        {warning}
                      </div>
                    ))}
                  </div>
                )}
                
                {foodCheckResult.recommendations.length > 0 && (
                  <div className="mt-4">
                    <h3 className="font-semibold mb-2">💡 Recommendations</h3>
                    {foodCheckResult.recommendations.map((rec: string, idx: number) => (
                      <p key={idx} className="text-sm mb-1">{rec}</p>
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
            <form onSubmit={handleGenerateMealPlan} className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
              <h2 className="text-xl font-semibold mb-4">Generate Meal Plan</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2">Medical Condition *</label>
                  <input
                    type="text"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    placeholder="e.g., Type 2 Diabetes, Hypertension"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Number of Days</label>
                  <input
                    type="number"
                    value={mealPlanDays}
                    onChange={(e) => setMealPlanDays(parseInt(e.target.value))}
                    min="1"
                    max="14"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm mb-2">Dietary Restrictions (optional)</label>
                  <input
                    type="text"
                    value={dietaryRestrictions}
                    onChange={(e) => setDietaryRestrictions(e.target.value)}
                    placeholder="e.g., Vegetarian, Gluten-free"
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-white"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-zinc-700 text-white font-semibold py-3 px-6 rounded-lg"
                >
                  {loading ? 'Generating Meal Plan...' : 'Generate Meal Plan'}
                </button>
              </div>
            </form>

            {mealPlan && !mealPlan.error && (
              <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700 space-y-4">
                <h2 className="text-xl font-semibold">{mealPlanDays}-Day Meal Plan for {condition}</h2>
                
                {mealPlan.meal_plan && mealPlan.meal_plan.map((day: any, idx: number) => (
                  <div key={idx} className="bg-zinc-900 rounded-lg p-4 border border-zinc-700">
                    <h3 className="font-semibold mb-2">Day {day.day}</h3>
                    <div className="space-y-2 text-sm">
                      <p><strong>Breakfast:</strong> {day.breakfast?.meal}</p>
                      <p><strong>Lunch:</strong> {day.lunch?.meal}</p>
                      <p><strong>Dinner:</strong> {day.dinner?.meal}</p>
                      <p><strong>Snacks:</strong> {day.snacks?.join(', ')}</p>
                    </div>
                  </div>
                ))}
                
                {mealPlan.shopping_list && (
                  <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-400 mb-2">🛒 Shopping List</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm">
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

        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200 mt-4">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
