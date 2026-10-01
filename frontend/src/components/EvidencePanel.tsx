/**
 * Sprint 4: EvidencePanel Component
 *
 * Shows evidence for a financial fact:
 * - Value and prior year value
 * - Growth percentage
 * - Source document and page
 * - Link to open PDF
 */
'use client';

import { useState } from 'react';

interface FinancialFact {
  id: number;
  metric: string;
  value: number;
  unit: string;
  source_page?: number;
  validation_status: string;
}

interface Source {
  id: number;
  title: string;
  document_date?: string;
  url?: string;
  file_path?: string;
}

interface EvidencePanelProps {
  fact: FinancialFact;
  priorFact?: FinancialFact;
  source?: Source;
  onClose: () => void;
}

export function EvidencePanel({ fact, priorFact, source, onClose }: EvidencePanelProps) {
  const growth = priorFact
    ? (((fact.value - priorFact.value) / Math.abs(priorFact.value)) * 100).toFixed(2)
    : null;

  const getValidationBadge = (status: string) => {
    switch (status) {
      case 'validated':
        return <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Validated</span>;
      case 'flagged':
        return <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Flagged</span>;
      default:
        return <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">Pending</span>;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b">
          <div>
            <h3 className="font-semibold text-lg capitalize">
              {fact.metric.replace(/_/g, ' ')}
            </h3>
            <p className="text-sm text-gray-600">Evidence & Traceability</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Current Value */}
          <div>
            <div className="text-sm text-gray-600">Current Value</div>
            <div className="text-3xl font-bold">
              {fact.value.toLocaleString('en-US', { maximumFractionDigits: 2 })} {fact.unit}
            </div>
          </div>

          {/* Prior Year & Growth */}
          {priorFact && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">Prior Year</div>
                <div className="text-lg font-semibold">
                  {priorFact.value.toLocaleString('en-US', { maximumFractionDigits: 2 })} {priorFact.unit}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Growth</div>
                <div className={`text-lg font-semibold ${parseFloat(growth!) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {growth}%
                </div>
              </div>
            </div>
          )}

          {/* Validation Status */}
          <div>
            <div className="text-sm text-gray-600 mb-2">Validation Status</div>
            {getValidationBadge(fact.validation_status)}
          </div>

          {/* Source Information */}
          {source && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Source</div>
              <div className="font-semibold text-sm">{source.title}</div>
              {source.document_date && (
                <div className="text-xs text-gray-600 mt-1">
                  Date: {new Date(source.document_date).toLocaleDateString()}
                </div>
              )}
              {fact.source_page && (
                <div className="text-xs text-gray-600">Page: {fact.source_page}</div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium"
            >
              Close
            </button>
            {source?.url && (
              <button
                onClick={() => window.open(source.url, '_blank')}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Open PDF
              </button>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t text-xs text-gray-600 rounded-b-lg">
          Every number in Khronos is traceable to its source. Click on any metric to see evidence.
        </div>
      </div>
    </div>
  );
}
