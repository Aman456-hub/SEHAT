import React, { useState } from 'react';
import { Search, Plus, Pill } from 'lucide-react';

/**
 * MedicineSearch Component
 * Renders an autocomplete search box for medicines.
 * Displays matching generic and brand names, letting chemists add items to their stock management lists.
 *
 * @component
 * @param {Object} props
 * @param {Array<Object>} props.results - Matching medicines from autocomplete query.
 * @param {function(string): void} props.onSearch - Callback triggered on text change to execute API queries.
 * @param {function(number): void} props.onSelect - Callback fired when a medicine is selected to add to stock.
 * @param {function(): void} props.onClear - Callback to clear the search result list state.
 */
export function MedicineSearch({ results, onSearch, onSelect, onClear }) {
  const [query, setQuery] = useState('');

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    onSearch(val);
  };

  const handleSelect = (id) => {
    onSelect(id);
    setQuery('');
    onClear();
  };

  return (
    <div className="relative w-full max-w-xl">
      {/* Search Input Box */}
      <div className="relative flex items-center">
        <Search className="absolute left-4 h-5 w-5 text-slate-500 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder="Search generic (e.g. Paracetamol) or brand (e.g. Crocin)..."
          className="w-full bg-slate-900/60 border border-slate-800/80 rounded-2xl py-3.5 pl-12 pr-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition-all shadow-inner"
        />
      </div>

      {/* Autocomplete Dropdown */}
      {query.trim() && results.length > 0 && (
        <div className="absolute z-30 w-full mt-2 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-2xl shadow-2xl overflow-hidden divide-y divide-slate-800/40">
          <ul className="max-h-60 overflow-y-auto">
            {results.map((med) => (
              <li key={med.id}>
                <button
                  type="button"
                  onClick={() => handleSelect(med.id)}
                  className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-slate-800/50 text-left transition-colors duration-150"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400">
                      <Pill className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-semibold text-white block">
                        {med.generic_name}
                      </span>
                      <span className="text-xs text-slate-400 block mt-0.5">
                        Brands: {med.brand_names.join(', ')} • Schedule {med.schedule}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center text-xs font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-xl hover:bg-indigo-500 hover:text-white transition-all">
                    <Plus className="h-3 w-3 mr-1" /> Add Stock
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Empty State indicator */}
      {query.trim() && results.length === 0 && (
        <div className="absolute z-30 w-full mt-2 bg-slate-900/90 border border-slate-800/80 rounded-2xl p-4 text-center text-sm text-slate-500 shadow-xl">
          No medicines found matching "{query}"
        </div>
      )}
    </div>
  );
}

export default MedicineSearch;
