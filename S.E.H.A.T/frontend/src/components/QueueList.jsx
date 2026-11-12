import React from 'react';
import { User, Phone, Clock, Check, X, Volume2 } from 'lucide-react';

/**
 * QueueList Component
 * Displays a premium list of patients currently in the doctor's queue.
 * Distinguishes the currently called patient (active) from waiting patients.
 * Provides interactive actions for queue state transitions.
 *
 * @component
 * @param {Object} props
 * @param {Array<Object>} props.tokens - Array of QueueToken objects from the API.
 * @param {function(number): void} props.onCall - Action callback to call a waiting patient.
 * @param {function(number): void} props.onSeen - Action callback to complete a session.
 * @param {function(number): void} props.onCancel - Action callback to cancel a patient's token.
 */
export function QueueList({ tokens, onCall, onSeen, onCancel }) {
  if (tokens.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center bg-slate-900/30 border border-dashed border-slate-800 rounded-3xl backdrop-blur-sm">
        <User className="h-12 w-12 text-slate-600 mb-4 animate-pulse" />
        <h3 className="text-lg font-semibold text-slate-300">Queue is Empty</h3>
        <p className="text-sm text-slate-500 max-w-xs mt-1">
          When patients book tokens via WhatsApp, they will appear here in real-time.
        </p>
      </div>
    );
  }

  // Segment active called patient from waiting list
  const calledPatient = tokens.find((t) => t.status === 'called');
  const waitingPatients = tokens.filter((t) => t.status === 'waiting');

  return (
    <div className="space-y-6">
      {/* 1. Currently Called / Inside Clinic Card */}
      {calledPatient ? (
        <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900/40 via-indigo-950/40 to-slate-900/40 backdrop-blur-md border-2 border-indigo-500/80 rounded-3xl p-6 shadow-[0_0_30px_rgba(99,102,241,0.25)] transition-all duration-300">
          {/* Glowing pulse indicator */}
          <div className="absolute top-0 right-0 mt-4 mr-4 flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
              Currently Inside
            </span>
          </div>

          <span className="text-xs uppercase tracking-widest text-indigo-400 font-bold block mb-1">
            Active Consultation
          </span>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-2">
            <div className="flex items-start space-x-4">
              <div className="h-14 w-14 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-extrabold text-2xl">
                #{calledPatient.token_number}
              </div>
              <div>
                <h4 className="text-xl font-bold text-white flex items-center gap-2">
                  {calledPatient.patient_name}
                </h4>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-slate-400 text-sm mt-1">
                  <span className="flex items-center gap-1">
                    <Phone className="h-3 w-3 text-slate-500" />
                    {calledPatient.patient_phone}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-slate-500" />
                    Called at {new Date(calledPatient.called_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 self-end md:self-center">
              <button
                onClick={() => onCancel(calledPatient.id)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500 hover:text-white text-rose-400 transition-all duration-200"
              >
                <X className="h-4 w-4" /> Absent / Cancel
              </button>
              <button
                onClick={() => onSeen(calledPatient.id)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 hover:bg-indigo-400 text-white shadow-[0_4px_15px_rgba(99,102,241,0.3)] hover:shadow-[0_4px_20px_rgba(99,102,241,0.5)] transition-all duration-200"
              >
                <Check className="h-4 w-4" /> Complete / Next
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800 p-6 rounded-3xl text-center">
          <p className="text-slate-400 font-medium">No patient inside yet.</p>
          <button
            onClick={() => {
              if (waitingPatients.length > 0) {
                onCall(waitingPatients[0].id);
              }
            }}
            disabled={waitingPatients.length === 0}
            className="mt-3 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Volume2 className="h-4 w-4" /> Call First Patient
          </button>
        </div>
      )}

      {/* 2. Waitlist Queue list */}
      <div className="bg-slate-900/20 backdrop-blur-sm border border-slate-800/80 rounded-3xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/60 bg-slate-900/45 flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Waiting List ({waitingPatients.length} Patients)
          </h3>
        </div>

        <ul className="divide-y divide-slate-800/45 max-h-[480px] overflow-y-auto">
          {waitingPatients.map((token, index) => {
            const isNext = index === 0;
            return (
              <li
                key={token.id}
                className={`p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors duration-150 ${
                  isNext ? 'bg-indigo-500/5' : 'hover:bg-slate-900/10'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div className={`h-11 w-11 rounded-xl flex items-center justify-center font-extrabold text-lg ${
                    isNext ? 'bg-indigo-500/20 border border-indigo-500/40 text-indigo-300' : 'bg-slate-800 text-slate-400'
                  }`}>
                    #{token.token_number}
                  </div>
                  <div>
                    <h5 className="font-bold text-white flex items-center gap-2">
                      {token.patient_name}
                      {isNext && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-extrabold uppercase tracking-wide bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">
                          Next Up
                        </span>
                      )}
                    </h5>
                    <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3 text-slate-500" />
                        {token.patient_phone}
                      </span>
                      <span className="text-slate-600">•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-slate-500" />
                        Est. Wait: {token.estimated_wait_minutes} mins
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center">
                  <button
                    onClick={() => onCancel(token.id)}
                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                    title="Cancel Token"
                  >
                    <X className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => onCall(token.id)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold bg-indigo-500/10 border border-indigo-500/30 hover:bg-indigo-500 text-indigo-300 hover:text-white transition-all duration-200"
                  >
                    <Volume2 className="h-4 w-4" /> Call Turn
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default QueueList;
