import React from 'react';
import { Pill, AlertTriangle, Clock } from 'lucide-react';

/**
 * StockToggle Component
 * Renders an inventory card for a single stocked medicine.
 * Allows toggling availability and displays staleness warnings if not updated within 24 hours.
 *
 * @component
 * @param {Object} props
 * @param {Object} props.stockItem - ChemistStock object containing medicine relationships.
 * @param {function(number, boolean): void} props.onToggle - Callback triggered when toggle switch changes.
 */
export function StockToggle({ stockItem, onToggle }) {
  const { medicine, is_available, last_updated } = stockItem;

  // Check staleness (Business Rule 3: Stale after 24 hours)
  const isStale = () => {
    const updatedTime = new Date(last_updated);
    const now = new Date();
    const diffHours = (now - updatedTime) / (1000 * 60 * 60);
    return diffHours >= 24;
  };

  const formatLastUpdated = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const staleStatus = isStale();

  return (
    <div className={`relative overflow-hidden bg-slate-900/40 backdrop-blur-md border rounded-2xl p-5 shadow-lg transition-all duration-300 ${
      is_available
        ? 'border-slate-800 hover:border-indigo-500/40'
        : 'border-slate-850 opacity-75'
    }`}>
      {/* Staleness Banner Warning */}
      {staleStatus && (
        <div className="absolute top-0 left-0 w-full bg-amber-500/10 border-b border-amber-500/25 px-4 py-1 flex items-center space-x-2 text-[10px] font-bold text-amber-400 uppercase tracking-wider">
          <AlertTriangle className="h-3.5 w-3.5 animate-pulse" />
          <span>Stale Stock Data (Last updated &gt; 24h ago)</span>
        </div>
      )}

      <div className={`flex flex-col justify-between h-full ${staleStatus ? 'pt-6' : ''}`}>
        {/* Medicine Metadata */}
        <div>
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2.5 rounded-xl border ${
                is_available
                  ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                  : 'bg-slate-800 border-slate-700 text-slate-500'
              }`}>
                <Pill className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-bold text-white text-base leading-tight">
                  {medicine.generic_name}
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-tight">
                  Brands: {medicine.brand_names.join(', ')}
                </p>
              </div>
            </div>

            {/* Availability Toggle Button Switch */}
            <button
              type="button"
              onClick={() => onToggle(medicine.id, !is_available)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950 ${
                is_available ? 'bg-indigo-500' : 'bg-slate-700'
              }`}
            >
              <span className="sr-only">Toggle medicine stock</span>
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  is_available ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="text-[10px] font-extrabold uppercase tracking-wide bg-slate-800 border border-slate-700/60 px-2 py-1 rounded-lg text-slate-400">
              {medicine.category}
            </span>
            <span className={`text-[10px] font-extrabold uppercase tracking-wide px-2 py-1 rounded-lg border ${
              medicine.schedule.startsWith('H')
                ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            }`}>
              Schedule {medicine.schedule}
            </span>
            <span className={`text-[10px] font-bold px-2 py-1 rounded-lg border flex items-center space-x-1 ${
              is_available
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-slate-800 border-slate-700 text-slate-500'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full mr-1 ${is_available ? 'bg-emerald-400' : 'bg-slate-500'}`} />
              {is_available ? 'In Stock' : 'Out of Stock'}
            </span>
          </div>
        </div>

        {/* Timestamp */}
        <div className="mt-4 pt-3 border-t border-slate-800/40 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Last checked:
          </span>
          <span className="font-mono text-slate-400">
            {formatLastUpdated(last_updated)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default StockToggle;
