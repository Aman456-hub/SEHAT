import React, { useState } from 'react';
import { Plus, Minus, Check } from 'lucide-react';

/**
 * BloodStockForm Component
 * Renders adjustment inputs for modifying blood stock inventory units.
 *
 * @component
 * @param {Object} props
 * @param {Array} props.stocks - Current blood bank stocks list
 * @param {function} props.onUpdateStock - Action trigger callback to update group stock units
 */
export function BloodStockForm({ stocks, onUpdateStock }) {
  const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'];
  const [inputs, setInputs] = useState({});

  const handleInputChange = (group, val) => {
    const numericVal = parseInt(val, 10);
    setInputs(prev => ({
      ...prev,
      [group]: isNaN(numericVal) ? '' : Math.max(0, numericVal)
    }));
  };

  const getUnits = (group) => {
    const existing = stocks.find(s => s.blood_group === group);
    return existing ? existing.units_available : 0;
  };

  const handleAdjustment = (group, diff) => {
    const currentInputVal = inputs[group];
    const baseVal = (currentInputVal !== undefined && currentInputVal !== '') ? currentInputVal : getUnits(group);
    const targetVal = Math.max(0, baseVal + diff);
    setInputs(prev => ({
      ...prev,
      [group]: targetVal
    }));
  };

  const handleSave = (group) => {
    const val = inputs[group];
    if (val !== undefined && val !== '') {
      onUpdateStock(group, val);
      setInputs(prev => ({ ...prev, [group]: '' }));
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {bloodGroups.map((group) => {
          const currentUnits = getUnits(group);
          const inputValue = inputs[group] !== undefined ? inputs[group] : '';
          
          return (
            <div key={group} className="bg-slate-900/20 border border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-2xl font-extrabold text-white block">{group}</span>
                <span className="text-xs text-slate-500 font-bold uppercase tracking-wider block mt-0.5">
                  Current: {currentUnits} units
                </span>
              </div>

              {/* Adjusters */}
              <div className="flex items-center space-x-2 mt-4">
                <button
                  type="button"
                  onClick={() => handleAdjustment(group, -1)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-xl transition duration-150"
                >
                  <Minus className="h-4 w-4" />
                </button>
                
                <input
                  type="number"
                  placeholder={currentUnits.toString()}
                  value={inputValue}
                  onChange={(e) => handleInputChange(group, e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-white font-mono text-center rounded-xl py-1.5 w-16 focus:outline-none focus:border-indigo-500/50 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-sm"
                />

                <button
                  type="button"
                  onClick={() => handleAdjustment(group, 1)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-xl transition duration-150"
                >
                  <Plus className="h-4 w-4" />
                </button>

                <button
                  type="button"
                  onClick={() => handleSave(group)}
                  disabled={inputValue === ''}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white p-2 rounded-xl transition duration-150 shadow-md shadow-indigo-600/10"
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default BloodStockForm;
