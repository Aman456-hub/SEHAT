import React from 'react';

/**
 * ToggleButton Component
 * Renders a premium, animated glassmorphic status toggle for doctor clinic availability.
 *
 * @component
 * @param {Object} props
 * @param {boolean} props.isAvailable - True if the doctor is currently online/available.
 * @param {function(boolean): void} props.onChange - Callback fired when the toggle changes state.
 * @param {boolean} [props.disabled=false] - If true, disables the toggle interaction.
 */
export function ToggleButton({ isAvailable, onChange, disabled = false }) {
  return (
    <div className="flex items-center space-x-4 bg-slate-900/50 backdrop-blur-md border border-slate-800/80 p-4 rounded-2xl shadow-xl transition-all duration-300">
      <div className="flex flex-col">
        <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          Clinic Status
        </span>
        <span className={`text-sm font-bold transition-colors duration-300 ${
          isAvailable ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.2)]' : 'text-rose-400 drop-shadow-[0_0_10px_rgba(251,113,133,0.2)]'
        }`}>
          {isAvailable ? 'Available & Accepting Patients' : 'Offline / Closed'}
        </span>
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(!isAvailable)}
        className={`relative inline-flex h-8 w-16 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950 ${
          isAvailable ? 'bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'bg-slate-700'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span className="sr-only">Toggle doctor availability</span>
        <span
          aria-hidden="true"
          className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow-md ring-0 transition duration-300 ease-in-out ${
            isAvailable ? 'translate-x-8' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

export default ToggleButton;
