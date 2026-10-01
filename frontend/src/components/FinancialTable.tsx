/**
 * Sprint 4: FinancialTable Component
 *
 * Displays financial facts in a table format.
 * Click on values to open EvidencePanel.
 */
'use client';

import { useState } from 'react';
import { EvidencePanel } from './EvidencePanel';

interface FinancialFact {
  id: number;
  metric: string;
  value: number;
  unit: string;
  statement_type: string;
  source_id: number;
  source_page?: number;
  validation_status: string;
}

interface Source {
  id: number;
  title: string;
  document_date?: string;
  url?: string;
}

interface FinancialTableProps {
  facts: FinancialFact[];
  sources: { [key: number]: Source };
  priorFacts?: { [key: string]: FinancialFact };
}

export function FinancialTable({ facts, sources, priorFacts = {} }: FinancialTableProps) {
  const [selectedFact, setSelectedFact] = useState<FinancialFact | null>(null);

  // Group facts by statement type
  const groupedFacts = facts.reduce((acc, fact) => {
    if (!acc[fact.statement_type]) {
      acc[fact.statement_type] = [];
    }
    acc[fact.statement_type].push(fact);
    return acc;
  }, {} as { [key: string]: FinancialFact[] });

  const formatValue = (value: number) => {
    return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
  };

  const getRowClassName = (status: string) => {
    if (status === 'flagged') return 'bg-yellow-50 hover:bg-yellow-100';
    return 'hover:bg-gray-50';
  };

  return (
    <>
      {Object.entries(groupedFacts).map(([statementType, statementFacts]) => (
        <div key={statementType} className="mb-8">
          <h3 className="text-lg font-semibold mb-4 capitalize">
            {statementType.replace(/_/g, ' ')}
          </h3>

          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-gray-300">
                <th className="text-left py-3 px-4 font-semibold">Metric</th>
                <th className="text-right py-3 px-4 font-semibold">Value</th>
                <th className="text-right py-3 px-4 font-semibold">Prior Year</th>
                <th className="text-right py-3 px-4 font-semibold">Growth %</th>
                <th className="text-center py-3 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {statementFacts.map(fact => {
                const priorFact = priorFacts[fact.metric];
                const growth = priorFact
                  ? (((fact.value - priorFact.value) / Math.abs(priorFact.value)) * 100).toFixed(1)
                  : null;

                return (
                  <tr
                    key={fact.id}
                    className={`border-b cursor-pointer transition ${getRowClassName(fact.validation_status)}`}
                    onClick={() => setSelectedFact(fact)}
                  >
                    <td className="py-3 px-4 capitalize">
                      {fact.metric.replace(/_/g, ' ')}
                    </td>
                    <td className="text-right py-3 px-4 font-semibold">
                      {formatValue(fact.value)} {fact.unit}
                    </td>
                    <td className="text-right py-3 px-4">
                      {priorFact ? `${formatValue(priorFact.value)} ${priorFact.unit}` : '—'}
                    </td>
                    <td className={`text-right py-3 px-4 ${growth && parseFloat(growth) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {growth ? `${growth}%` : '—'}
                    </td>
                    <td className="text-center py-3 px-4">
                      <span className={`inline-block px-2 py-1 text-xs rounded ${
                        fact.validation_status === 'validated'
                          ? 'bg-green-100 text-green-800'
                          : fact.validation_status === 'flagged'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {fact.validation_status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}

      {selectedFact && (
        <EvidencePanel
          fact={selectedFact}
          priorFact={priorFacts[selectedFact.metric]}
          source={sources[selectedFact.source_id]}
          onClose={() => setSelectedFact(null)}
        />
      )}
    </>
  );
}
