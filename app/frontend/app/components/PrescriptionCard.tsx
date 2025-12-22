'use client';

import type { PrescriptionInfo } from '../lib/types';

interface PrescriptionCardProps {
  prescription: PrescriptionInfo;
  index?: number;
}

export default function PrescriptionCard({ prescription, index }: PrescriptionCardProps) {
  return (
    <div className="medical-card p-5 border-2 border-blue-200 rounded-xl shadow-lg">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-bold shadow-md">
            {index !== undefined ? index + 1 : '💊'}
          </div>
          <div>
            <h3 className="font-bold text-lg text-slate-800">
              {prescription.medication_name || 'Unknown Medication'}
            </h3>
            {prescription.prescriber && (
              <p className="text-xs text-slate-600 mt-1">
                Prescribed by: <span className="font-semibold">{prescription.prescriber}</span>
              </p>
            )}
          </div>
        </div>
        {prescription.date && (
          <div className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
            {prescription.date}
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {prescription.dosage && (
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Dosage</p>
            <p className="text-sm font-bold text-slate-800">{prescription.dosage}</p>
          </div>
        )}
        {prescription.frequency && (
          <div className="bg-cyan-50 rounded-lg p-3 border border-cyan-100">
            <p className="text-xs font-semibold text-cyan-600 uppercase tracking-wide mb-1">Frequency</p>
            <p className="text-sm font-bold text-slate-800">{prescription.frequency}</p>
          </div>
        )}
        {prescription.quantity && (
          <div className="bg-teal-50 rounded-lg p-3 border border-teal-100">
            <p className="text-xs font-semibold text-teal-600 uppercase tracking-wide mb-1">Quantity</p>
            <p className="text-sm font-bold text-slate-800">{prescription.quantity}</p>
          </div>
        )}
        {prescription.refills && (
          <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-100">
            <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-1">Refills</p>
            <p className="text-sm font-bold text-slate-800">{prescription.refills}</p>
          </div>
        )}
      </div>

      {prescription.instructions && !prescription.instructions.includes('Error extracting') && (
        <div className="bg-amber-50 rounded-lg p-4 border-l-4 border-amber-400">
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-2">📋 Instructions</p>
          <p className="text-sm text-slate-700 leading-relaxed">{prescription.instructions}</p>
        </div>
      )}

      {prescription.instructions?.includes('Error extracting') && (
        <div className="bg-red-50 rounded-lg p-4 border-l-4 border-red-400">
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">⚠️ Extraction Issue</p>
          <p className="text-sm text-red-700">{prescription.instructions}</p>
        </div>
      )}
    </div>
  );
}

