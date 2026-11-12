import React, { useState, useEffect, useCallback } from 'react';
import { useQueue } from '../hooks/useQueue';
import { ToggleButton } from '../components/ToggleButton';
import { QueueList } from '../components/QueueList';
import { Users, Clock, Hash, Activity, FileText, Download, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';

/**
 * DoctorDashboard Page Component
 * Renders the live clinical dashboard for doctor availability toggle,
 * live stats monitoring, and real-time patient queue manipulation.
 *
 * @component
 */
export function DoctorDashboard() {
  const savedUser = JSON.parse(localStorage.getItem('sehat_user') || '{}');
  const userRole = localStorage.getItem('sehat_role') || 'doctor';

  const [activeDoctorId, setActiveDoctorId] = useState(savedUser?.id || 1);
  const [doctorsList, setDoctorsList] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [prescLoading, setPrescLoading] = useState(false);

  const {
    queue,
    doctor,
    loading,
    error,
    toggleAvailability,
    callPatient,
    seenPatient,
    cancelPatient,
  } = useQueue(activeDoctorId);

  // Fetch doctors list for Admin dropdown
  useEffect(() => {
    if (userRole === 'admin') {
      async function fetchDoctors() {
        const res = await api.get('/api/doctors');
        if (res.success) {
          setDoctorsList(res.data);
        }
      }
      fetchDoctors();
    }
  }, [userRole]);

  // Fetch prescription logs for clinical review
  const loadPrescriptions = useCallback(async () => {
    setPrescLoading(true);
    try {
      const res = await api.get('/api/doctors/prescriptions');
      if (res.success) {
        setPrescriptions(res.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setPrescLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPrescriptions();
  }, [loadPrescriptions]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-300">
        <Activity className="h-10 w-10 text-indigo-500 animate-spin mb-4" />
        <p className="text-sm font-semibold uppercase tracking-wider text-slate-400">Loading SEHAT Dashboard...</p>
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-300 p-6 text-center">
        <div className="bg-rose-500/10 border border-rose-500/20 p-8 rounded-3xl max-w-md">
          <h3 className="text-xl font-bold text-rose-400">Connection Failed</h3>
          <p className="text-slate-400 text-sm mt-2">
            Could not connect to the SEHAT backend. Please make sure the FastAPI server is running.
          </p>
          <p className="text-xs text-rose-400/70 font-mono mt-4 p-2 bg-slate-950/50 rounded-xl overflow-x-auto text-left">
            Error: {error || 'Doctor profile not found.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 w-full py-2.5 rounded-xl font-bold bg-rose-500 hover:bg-rose-400 text-white transition-all"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Calculate live statistics
  const totalWaiting = queue.filter((t) => t.status === 'waiting').length;
  const activeCalled = queue.filter((t) => t.status === 'called').length;
  const avgWait = doctor.avg_consultation_minutes;
  const totalEstWait = totalWaiting * avgWait;
  const nextToken = queue.length > 0 ? Math.max(...queue.map((t) => t.token_number)) + 1 : 1;

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
      {/* Header Panel */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-slate-800/80 mb-8">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-extrabold uppercase tracking-widest">
            <Activity className="h-4 w-4 animate-pulse" />
            <span>SEHAT Queue Coordinator {userRole === 'admin' && <span className="text-rose-450 font-bold ml-1.5 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wider">Admin Mode</span>}</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-1">
            Dr. {doctor.name}
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {doctor.specialization} • {doctor.clinic_name}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {userRole === 'admin' && doctorsList.length > 0 && (
            <div className="flex flex-col space-y-1">
              <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">Doctor Workspace Select</span>
              <select
                value={activeDoctorId}
                onChange={(e) => setActiveDoctorId(parseInt(e.target.value, 10))}
                className="bg-slate-900 border border-slate-850 hover:border-slate-800 text-slate-200 text-xs font-bold py-2 px-3 rounded-xl focus:outline-none focus:border-indigo-500/60 transition duration-150 cursor-pointer min-w-[200px]"
              >
                {doctorsList.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dr. {d.name} ({d.specialization})
                  </option>
                ))}
              </select>
            </div>
          )}
          <ToggleButton isAvailable={doctor.is_available} onChange={toggleAvailability} />
        </div>
      </header>

      {/* Stats Cards Section */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        {/* Waiting Card */}
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Waiting Patients</span>
            <span className="text-3xl font-extrabold text-white mt-1 block">
              {totalWaiting} <span className="text-sm font-medium text-slate-500">in queue</span>
            </span>
          </div>
        </div>

        {/* Est. Wait Card */}
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Est. Delay Time</span>
            <span className="text-3xl font-extrabold text-white mt-1 block">
              {totalEstWait} <span className="text-sm font-medium text-slate-500">mins total</span>
            </span>
          </div>
        </div>

        {/* Next Token Card */}
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl">
            <Hash className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Next New Token</span>
            <span className="text-3xl font-extrabold text-white mt-1 block">
              #{nextToken} <span className="text-sm font-medium text-slate-500">available</span>
            </span>
          </div>
        </div>
      </section>

      {/* Main Queue Management Area */}
      <main className="bg-slate-900/20 backdrop-blur-md border border-slate-800/60 rounded-3xl p-6 shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Activity className="h-5 w-5 text-indigo-500" /> Live Queue Board
        </h2>
        <QueueList
          tokens={queue}
          onCall={callPatient}
          onSeen={seenPatient}
          onCancel={cancelPatient}
        />
      </main>

      {/* Uploaded Prescriptions Clinical History */}
      <section className="mt-8 bg-slate-900/20 backdrop-blur-md border border-slate-800/60 rounded-3xl p-6 shadow-2xl select-none">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <FileText className="h-5 w-5 text-indigo-500" /> Patient Prescription Scan Log
        </h2>
        {prescLoading ? (
          <div className="flex justify-center py-8">
            <Clock className="h-6 w-6 text-indigo-500 animate-spin" />
          </div>
        ) : prescriptions.length === 0 ? (
          <p className="text-slate-500 text-xs text-center py-6 font-mono">No prescriptions uploaded or analyzed yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {prescriptions.map((log) => (
              <div key={log.id} className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-indigo-400 font-bold bg-indigo-500/10 px-2 py-0.5 rounded">
                    Patient Phone (SHA256 Hash): {log.patient_phone.slice(0, 16)}...
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                
                <div className="flex gap-4">
                  {log.image_url && (
                    <div className="relative group shrink-0">
                      <img
                        src={log.image_url}
                        alt="Prescription Scan"
                        className="w-20 h-20 object-cover rounded-lg border border-slate-800 hover:border-slate-700 transition"
                      />
                      <a
                        href={log.image_url}
                        target="_blank"
                        rel="noreferrer"
                        className="absolute inset-0 flex items-center justify-center bg-slate-950/80 text-white opacity-0 group-hover:opacity-100 transition rounded-lg"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1.5">Extracted Medicines</span>
                    <div className="flex flex-wrap gap-1">
                      {log.extracted_medicines && log.extracted_medicines.medicines && log.extracted_medicines.medicines.length > 0 ? (
                        log.extracted_medicines.medicines.map((m, idx) => (
                          <span key={idx} className="bg-slate-950 border border-slate-800 text-slate-300 text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg">
                            {m.name || m.generic_name} ({m.dosage || m.dosage_instruction})
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-600 text-[10px] font-mono">No specific medications extracted.</span>
                      )}
                    </div>
                  </div>
                </div>

                {log.hindi_explanation && (
                  <div className="bg-slate-950/60 border border-slate-850 p-3.5 rounded-xl">
                    <span className="text-[10px] text-amber-500 font-extrabold uppercase tracking-wider block mb-1">Hindi Translation & Dosage Summary</span>
                    <p className="text-xs text-slate-300 font-medium leading-relaxed font-mono whitespace-pre-line">
                      {log.hindi_explanation}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DoctorDashboard;
