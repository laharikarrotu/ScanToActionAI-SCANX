'use client';

import { useHealthScan } from '../context/HealthScanContext';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';

export default function Sidebar() {
  const pathname = usePathname();
  const { prescriptionData, interactionResult, dietData } = useHealthScan();
  const [expandedSection, setExpandedSection] = useState<string | null>('dashboard');

  const stats = {
    prescriptionsScanned: prescriptionData?.medications?.length || 0,
    interactionsChecked: interactionResult ? 1 : 0,
    dietPlansGenerated: dietData?.condition ? 1 : 0,
  };

  // Unique Navigation - Contextual based on current page
  const getContextualActions = () => {
    if (pathname === '/') {
      return [
        { icon: '📋', label: 'Scan Prescription', href: '/scan', color: 'blue' },
        { icon: '💊', label: 'Check Interactions', href: '/interactions', color: 'teal' },
        { icon: '🥗', label: 'Diet Portal', href: '/diet', color: 'emerald' },
      ];
    }
    if (pathname === '/scan') {
      return [
        { icon: '💊', label: 'Check Interactions', href: '/interactions', color: 'teal' },
        { icon: '💬', label: 'Chat Assistant', href: '/', color: 'blue' },
      ];
    }
    if (pathname === '/interactions') {
      return [
        { icon: '🥗', label: 'Get Diet Advice', href: '/diet', color: 'emerald' },
        { icon: '💬', label: 'Ask Questions', href: '/', color: 'blue' },
      ];
    }
    if (pathname === '/diet') {
      return [
        { icon: '💊', label: 'Check Interactions', href: '/interactions', color: 'teal' },
        { icon: '💬', label: 'Chat Assistant', href: '/', color: 'blue' },
      ];
    }
    return [];
  };

  // Medication Timeline - Unique Feature
  const getMedicationTimeline = () => {
    if (!prescriptionData?.medications || prescriptionData.medications.length === 0) return null;
    
    return prescriptionData.medications.map((med, idx) => ({
      id: idx,
      name: med.medication_name,
      dosage: med.dosage,
      frequency: med.frequency,
      date: prescriptionData.date || 'Recent',
    }));
  };

  // Health Insights - Unique Feature
  const getHealthInsights = () => {
    const insights = [];
    
    if (prescriptionData?.medications && prescriptionData.medications.length > 0) {
      insights.push({
        type: 'info',
        icon: '💊',
        title: 'Active Medications',
        message: `${prescriptionData.medications.length} medication${prescriptionData.medications.length > 1 ? 's' : ''} tracked`,
      });
    }
    
    if (interactionResult) {
      const majorCount = interactionResult.warnings?.major?.length || 0;
      const moderateCount = interactionResult.warnings?.moderate?.length || 0;
      if (majorCount > 0) {
        insights.push({
          type: 'warning',
          icon: '⚠️',
          title: 'Action Required',
          message: `${majorCount} major interaction${majorCount > 1 ? 's' : ''} detected`,
        });
      } else if (moderateCount > 0) {
        insights.push({
          type: 'info',
          icon: 'ℹ️',
          title: 'Monitor Closely',
          message: `${moderateCount} moderate interaction${moderateCount > 1 ? 's' : ''} found`,
        });
      } else {
        insights.push({
          type: 'success',
          icon: '✅',
          title: 'All Clear',
          message: 'No significant interactions detected',
        });
      }
    }
    
    if (dietData?.condition) {
      insights.push({
        type: 'info',
        icon: '🥗',
        title: 'Diet Plan Active',
        message: `Managing: ${dietData.condition}`,
      });
    }
    
    return insights;
  };

  const medicationTimeline = getMedicationTimeline();
  const contextualActions = getContextualActions();
  const healthInsights = getHealthInsights();

  return (
    <aside className="w-80 flex-shrink-0 bg-gradient-to-b from-white via-slate-50/30 to-white border-r border-slate-200/40 flex flex-col h-full overflow-y-auto scrollbar-thin">
      {/* Dashboard Section - Collapsible */}
      <div className="p-5 border-b border-slate-200/40">
        <button
          onClick={() => setExpandedSection(expandedSection === 'dashboard' ? null : 'dashboard')}
          className="w-full flex items-center justify-between mb-3 group"
        >
          <h2 className="text-base font-bold text-slate-800 tracking-tight">Health Dashboard</h2>
          <svg 
            className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSection === 'dashboard' ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {expandedSection === 'dashboard' && (
          <div className="grid grid-cols-2 gap-2.5 animate-in slide-up">
            <div className="bg-gradient-to-br from-blue-50/80 to-blue-100/40 rounded-xl p-3 border border-blue-200/50">
              <div className="text-xl mb-1">📋</div>
              <div className="text-xl font-bold text-blue-700">{stats.prescriptionsScanned}</div>
              <div className="text-[10px] text-slate-600 font-medium">Scanned</div>
            </div>
            <div className="bg-gradient-to-br from-teal-50/80 to-teal-100/40 rounded-xl p-3 border border-teal-200/50">
              <div className="text-xl mb-1">💊</div>
              <div className="text-xl font-bold text-teal-700">{stats.interactionsChecked}</div>
              <div className="text-[10px] text-slate-600 font-medium">Checked</div>
            </div>
            <div className="bg-gradient-to-br from-emerald-50/80 to-emerald-100/40 rounded-xl p-3 border border-emerald-200/50">
              <div className="text-xl mb-1">🥗</div>
              <div className="text-xl font-bold text-emerald-700">{stats.dietPlansGenerated}</div>
              <div className="text-[10px] text-slate-600 font-medium">Plans</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50/80 to-purple-100/40 rounded-xl p-3 border border-purple-200/50">
              <div className="text-xl mb-1">🔒</div>
              <div className="text-xl font-bold text-purple-700">100%</div>
              <div className="text-[10px] text-slate-600 font-medium">Secure</div>
            </div>
          </div>
        )}
      </div>

      {/* Health Insights - Unique Feature */}
      {healthInsights.length > 0 && (
        <div className="p-5 border-b border-slate-200/40">
          <button
            onClick={() => setExpandedSection(expandedSection === 'insights' ? null : 'insights')}
            className="w-full flex items-center justify-between mb-3 group"
          >
            <h3 className="text-sm font-bold text-slate-800">Health Insights</h3>
            <svg 
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSection === 'insights' ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {expandedSection === 'insights' && (
            <div className="space-y-2.5 animate-in slide-up">
              {healthInsights.map((insight, idx) => (
                <div 
                  key={idx}
                  className={`rounded-xl p-3 border ${
                    insight.type === 'warning' 
                      ? 'bg-amber-50/80 border-amber-200/50' 
                      : insight.type === 'success'
                      ? 'bg-emerald-50/80 border-emerald-200/50'
                      : 'bg-blue-50/80 border-blue-200/50'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <span className="text-base">{insight.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-slate-800 mb-0.5">{insight.title}</p>
                      <p className="text-[11px] text-slate-600 leading-relaxed">{insight.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Medication Timeline - Unique Feature */}
      {medicationTimeline && medicationTimeline.length > 0 && (
        <div className="p-5 border-b border-slate-200/40">
          <button
            onClick={() => setExpandedSection(expandedSection === 'timeline' ? null : 'timeline')}
            className="w-full flex items-center justify-between mb-3 group"
          >
            <h3 className="text-sm font-bold text-slate-800">Medication Timeline</h3>
            <svg 
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSection === 'timeline' ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {expandedSection === 'timeline' && (
            <div className="space-y-2.5 animate-in slide-up">
              {medicationTimeline.map((med, idx) => (
                <div key={med.id} className="relative pl-4 border-l-2 border-blue-200/50">
                  <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-blue-500"></div>
                  <div className="bg-gradient-to-br from-slate-50/80 to-slate-100/40 rounded-lg p-2.5 border border-slate-200/50">
                    <p className="text-xs font-semibold text-slate-800 mb-1">{med.name}</p>
                    <p className="text-[11px] text-slate-600">{med.dosage} • {med.frequency}</p>
                    <p className="text-[10px] text-slate-400 mt-1">{med.date}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Contextual Quick Actions - Dynamic based on page */}
      {contextualActions.length > 0 && (
        <div className="p-5 border-b border-slate-200/40">
          <h3 className="text-sm font-bold text-slate-800 mb-3">Quick Actions</h3>
          <div className="space-y-2">
            {contextualActions.map((action) => {
              const colorClasses = {
                blue: 'from-blue-500 to-blue-600 border-blue-200/50',
                teal: 'from-teal-500 to-teal-600 border-teal-200/50',
                emerald: 'from-emerald-500 to-emerald-600 border-emerald-200/50',
              };
              
              return (
                <Link
                  key={action.href}
                  href={action.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-gradient-to-r ${colorClasses[action.color as keyof typeof colorClasses]} text-white text-sm font-medium shadow-sm hover:shadow-md hover:scale-[1.02] active:scale-95 transition-all duration-200`}
                >
                  <span className="text-base">{action.icon}</span>
                  <span>{action.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Smart Suggestions - Unique Feature */}
      <div className="p-5 flex-1">
        <h3 className="text-sm font-bold text-slate-800 mb-3">Smart Suggestions</h3>
        <div className="space-y-2.5">
          {!prescriptionData && (
            <div className="bg-gradient-to-br from-blue-50/60 to-blue-100/30 rounded-xl p-3 border border-blue-200/40">
              <p className="text-xs text-slate-700 leading-relaxed">
                💡 <strong>Start here:</strong> Upload a prescription to unlock personalized health insights
              </p>
            </div>
          )}
          {prescriptionData && !interactionResult && (
            <div className="bg-gradient-to-br from-teal-50/60 to-teal-100/30 rounded-xl p-3 border border-teal-200/40">
              <p className="text-xs text-slate-700 leading-relaxed">
                💊 <strong>Next step:</strong> Check for drug interactions to ensure medication safety
              </p>
            </div>
          )}
          {prescriptionData && interactionResult && !dietData && (
            <div className="bg-gradient-to-br from-emerald-50/60 to-emerald-100/30 rounded-xl p-3 border border-emerald-200/40">
              <p className="text-xs text-slate-700 leading-relaxed">
                🥗 <strong>Complete your health plan:</strong> Get personalized diet recommendations
              </p>
            </div>
          )}
          {prescriptionData && interactionResult && dietData && (
            <div className="bg-gradient-to-br from-purple-50/60 to-purple-100/30 rounded-xl p-3 border border-purple-200/40">
              <p className="text-xs text-slate-700 leading-relaxed">
                ✅ <strong>Great progress!</strong> You've completed the full HealthScan workflow
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
