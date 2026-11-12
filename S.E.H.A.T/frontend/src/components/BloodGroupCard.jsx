import React from 'react';
import { AlertCircle, Clock } from 'lucide-react';

/**
 * BloodGroupCard Component
 * Displays available units for a specific blood group along with a staleness verification alert.
 *
 * @component
 * @param {Object} props
 * @param {Object} props.stock - The blood stock database object
 * @param {string} props.group - The blood group name (e.g. "B+")
 */
export function BloodGroupCard({ stock, group }) {
  const units = stock?.units_available || 0;
  const lastUpdated = stock?.last_updated;

  // Determine if stock is stale (> 12 hours since last update)
  const getStaleness = () => {
    if (!lastUpdated) return true;
    const updateTime = new Date(lastUpdated).getTime();
    const twelveHoursAgo = Date.now() - 12 * 60 * 60 * 1000;
    return updateTime < twelveHoursAgo;
  };

  const isStale = getStaleness();

  return (
    <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between h-36">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-slate-500 uppercase tracking-widest">
          Group
        </span>
        {isStale && units > 0 && (
          <div className="flex items-center space-x-1 text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full text-[9px] font-bold">
            <AlertCircle className="h-3 w-3" />
            <span>UNVERIFIED</span>
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between mt-2">
        <h3 className="text-3xl font-extrabold text-white tracking-tight">
          {group}
        </h3>
        <div className="text-right">
          <span className="text-3xl font-extrabold text-indigo-400">
            {units}
          </span>
          <span className="text-xs text-slate-500 font-bold ml-1">
            units
          </span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/40 flex items-center justify-between text-[9px] font-bold text-slate-600 tracking-wider">
        <div className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>LAST UPDATED:</span>
        </div>
        <span>
          {lastUpdated ? new Date(lastUpdated).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'NEVER'}
        </span>
      </div>
    </div>
  );
}

export default BloodGroupCard;
