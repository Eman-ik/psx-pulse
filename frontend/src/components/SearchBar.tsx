/**
 * Sprint 4: SearchBar Component
 *
 * Allows users to search for companies by ticker or name.
 */
'use client';

import { API_BASE_URL } from "@/lib/config";
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface Company {
  id: number;
  ticker: string;
  name: string;
  sector: string;
  coverage_tier: string;
}

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Company[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch companies on query change
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    fetch(`${API_BASE_URL}/companies/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        setResults(data || []);
        setIsOpen(true);
      })
      .catch(err => {
        console.error('Search error:', err);
        setResults([]);
      })
      .finally(() => setLoading(false));
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getCoverageBadgeColor = (tier: string) => {
    switch (tier) {
      case 'full': return 'bg-green-100 text-green-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="relative w-full max-w-md" ref={dropdownRef}>
      <input
        type="text"
        placeholder="Search companies (ticker or name)..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-300 rounded-lg shadow-lg z-10">
          {loading && (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          )}

          {!loading && results.length === 0 && query && (
            <div className="p-4 text-center text-gray-500">No companies found</div>
          )}

          {results.map(company => (
            <Link
              key={company.id}
              href={`/company/${company.ticker}`}
              onClick={() => setIsOpen(false)}
              className="block p-3 hover:bg-gray-100 border-b last:border-b-0"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold">{company.ticker}</div>
                  <div className="text-sm text-gray-600">{company.name}</div>
                  <div className="text-xs text-gray-500">{company.sector}</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${getCoverageBadgeColor(company.coverage_tier)}`}>
                  {company.coverage_tier.toUpperCase()}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
