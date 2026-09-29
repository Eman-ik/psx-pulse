"use client";
import React, { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Globe,
  Factory,
} from "lucide-react";

interface BusinessModel {
  company_name: string;
  sector: string;
  what_it_sells: string;
  customer_segments: string[];
  revenue_sources: Record<string, string>;
  business_model: string;
  cost_structure: Record<string, string>;
  cyclicality: string;
  revenue_recurring: string;
  export_exposure: string;
  import_dependency: string;
  regulatory_risk: string;
  competitors: string[];
  competitive_advantages: string[];
  economic_moat: string;
  key_risks: string[];
}

export function BusinessModelSection({ ticker }: { ticker: string }) {
  const [data, setData] = useState<BusinessModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;

    const fetchBusinessModel = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `http://localhost:5000/api/research/${ticker}/business-model`
        );
        const result = await response.json();
        if (result.success) {
          setData(result.business_model);
        } else {
          setError("Business model data not available");
        }
      } catch (err) {
        setError("Failed to load business model");
      } finally {
        setLoading(false);
      }
    };

    fetchBusinessModel();
  }, [ticker]);

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 dark:bg-red-950 border border-red-200 rounded-lg">
        <p className="text-red-700 dark:text-red-200">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* What it Sells */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-2 mb-3">
          <Factory className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="font-semibold text-lg">What It Sells</h3>
        </div>
        <p className="text-gray-700 dark:text-gray-300">{data.what_it_sells}</p>
      </div>

      {/* Business Model */}
      <div className="bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 rounded-lg p-6 border border-purple-200 dark:border-purple-800">
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          <h3 className="font-semibold text-lg">Business Model</h3>
        </div>
        <p className="text-gray-700 dark:text-gray-300">
          {data.business_model}
        </p>
      </div>

      {/* Two-Column Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Revenue Sources */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="font-semibold mb-4">Revenue Sources</h3>
          <ul className="space-y-2">
            {Object.entries(data.revenue_sources).map(([source, pct]) => (
              <li
                key={source}
                className="flex justify-between text-sm text-gray-700 dark:text-gray-300"
              >
                <span>{source}</span>
                <span className="font-semibold text-blue-600 dark:text-blue-400">
                  {pct}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Customer Segments */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="font-semibold mb-4">Customer Segments</h3>
          <ul className="space-y-2">
            {data.customer_segments.map((segment) => (
              <li
                key={segment}
                className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2"
              >
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400" />
                <span>{segment}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Cost Structure */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="font-semibold mb-4">Cost Structure</h3>
          <ul className="space-y-2">
            {Object.entries(data.cost_structure).map(([cost, pct]) => (
              <li key={cost} className="text-sm text-gray-700 dark:text-gray-300">
                <div className="flex justify-between">
                  <span>{cost}</span>
                  <span className="font-semibold text-red-600 dark:text-red-400">
                    {pct}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Competitive Advantages */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="font-semibold mb-4">Competitive Advantages</h3>
          <ul className="space-y-2">
            {data.competitive_advantages.map((adv) => (
              <li
                key={adv}
                className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2"
              >
                <TrendingUp className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400" />
                <span>{adv}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Key Characteristics */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
        <h3 className="font-semibold mb-4">Key Characteristics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Cyclicality
            </p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {data.cyclicality}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Revenue Recurring
            </p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {data.revenue_recurring}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Export Exposure
            </p>
            <p className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {data.export_exposure}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Import Dependency
            </p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {data.import_dependency}
            </p>
          </div>
        </div>
      </div>

      {/* Economic Moat & Regulatory Risk */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 rounded-lg p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
            <h3 className="font-semibold">Economic Moat</h3>
          </div>
          <p className="text-gray-700 dark:text-gray-300 font-semibold text-lg mb-2">
            {data.economic_moat}
          </p>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 rounded-lg p-6 border border-orange-200 dark:border-orange-800">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <h3 className="font-semibold">Regulatory Risk</h3>
          </div>
          <p className="text-gray-700 dark:text-gray-300 font-semibold text-lg">
            {data.regulatory_risk}
          </p>
        </div>
      </div>

      {/* Competitors */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
        <h3 className="font-semibold mb-4">Competitors</h3>
        <div className="flex flex-wrap gap-2">
          {data.competitors.map((comp) => (
            <span
              key={comp}
              className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium"
            >
              {comp}
            </span>
          ))}
        </div>
      </div>

      {/* Key Risks */}
      <div className="bg-red-50 dark:bg-red-950 rounded-lg p-6 border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <h3 className="font-semibold text-red-900 dark:text-red-100">
            Key Risks
          </h3>
        </div>
        <ul className="space-y-2">
          {data.key_risks.map((risk) => (
            <li
              key={risk}
              className="text-sm text-red-800 dark:text-red-200 flex items-start gap-2"
            >
              <span className="text-red-600 dark:text-red-400 font-bold mt-0.5">
                •
              </span>
              <span>{risk}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
