/**
 * Sprint 4: Search Page
 *
 * Main entry point for finding companies.
 */
'use client';

import { SearchBar } from '@/components/SearchBar';

export default function SearchPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold mb-2">Khronos</h1>
          <p className="text-gray-600">Financial data you can trust. Every number traceable to source.</p>
        </div>
      </div>

      {/* Search Section */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold mb-6">Find a Company</h2>
          <SearchBar />

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="text-2xl font-bold text-blue-600 mb-2">3</div>
              <div className="text-gray-700">Companies analyzed</div>
              <div className="text-sm text-gray-600">Lucky Cement, DGKC, CHCC</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 mb-2">90+</div>
              <div className="text-gray-700">Financial facts</div>
              <div className="text-sm text-gray-600">Income, balance sheet, cash flow</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600 mb-2">17</div>
              <div className="text-gray-700">Calculated metrics</div>
              <div className="text-sm text-gray-600">Margins, ratios, growth rates</div>
            </div>
          </div>

          {/* Features */}
          <div className="mt-12 border-t pt-8">
            <h3 className="font-semibold mb-6 text-gray-900">What you can do:</h3>
            <ul className="space-y-3 text-gray-700">
              <li className="flex items-start">
                <span className="text-green-600 mr-3">✓</span>
                <span>View financial statements from annual reports (income, balance sheet, cash flow)</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-3">✓</span>
                <span>See calculated metrics (margins, ROE, FCF, ratios) with formulas</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-3">✓</span>
                <span>Click any number to see the source document and page</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-3">✓</span>
                <span>Compare companies with peer metrics</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-3">✓</span>
                <span>Track trends across multiple years</span>
              </li>
            </ul>
          </div>

          {/* Data Quality Note */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>Data Quality:</strong> All financial facts are validated against accounting standards.
              Every number is traceable to its source document and page number.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-800 text-gray-300 py-8 mt-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-sm">
            Khronos Financial Research MVP • Sprint 4 Frontend
          </p>
        </div>
      </div>
    </main>
  );
}
