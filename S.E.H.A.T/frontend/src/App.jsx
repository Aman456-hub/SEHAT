import React, { useState, useEffect } from 'react';
import DoctorDashboard from './pages/DoctorDashboard.jsx';
import ChemistDashboard from './pages/ChemistDashboard.jsx';
import AdminDashboard from './pages/AdminDashboard.jsx';
import BloodBankDashboard from './pages/BloodBankDashboard.jsx';
import LoginPage from './pages/LoginPage.jsx';
import { LogOut, User, Activity } from 'lucide-react';

function App() {
  const [token, setToken] = useState(localStorage.getItem('sehat_token') || null);
  const [role, setRole] = useState(localStorage.getItem('sehat_role') || null);
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState('doctor');

  // Load user data safely from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem('sehat_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error('Error parsing user data:', e);
      }
    }
  }, [token]);

  // Set active tab based on role when logging in
  useEffect(() => {
    if (role) {
      setTab(role);
    }
  }, [role]);

  const handleLoginSuccess = (newToken, newRole, newUser) => {
    localStorage.setItem('sehat_token', newToken);
    localStorage.setItem('sehat_role', newRole);
    localStorage.setItem('sehat_user', JSON.stringify(newUser));
    setToken(newToken);
    setRole(newRole);
    setUser(newUser);
  };

  const handleLogout = () => {
    localStorage.removeItem('sehat_token');
    localStorage.removeItem('sehat_role');
    localStorage.removeItem('sehat_user');
    setToken(null);
    setRole(null);
    setUser(null);
  };

  // Auth gate - if not authenticated, show login page
  if (!token || !role) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Navigation Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800/60 px-6 py-3.5 flex items-center justify-between text-xs font-semibold select-none">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-indigo-400 font-bold tracking-wider uppercase">
            <Activity className="h-4 w-4 text-indigo-500 animate-pulse" />
            <span>SEHAT Platform</span>
          </div>
          {user && (
            <span className="hidden md:inline text-slate-500 font-mono text-[10px]">
              • Authenticated: {user.name} ({role.toUpperCase()})
            </span>
          )}
        </div>

        {/* Tab switcher options based on role */}
        <div className="flex items-center space-x-4">
          <div className="flex space-x-2 bg-slate-950/40 p-1 border border-slate-800/40 rounded-xl">
            {/* Admin has access to all tabs; others only see their role workspace */}
            {role === 'admin' ? (
              <>
                <button
                  type="button"
                  onClick={() => setTab('doctor')}
                  className={`px-3 py-1.5 rounded-lg transition-all font-bold ${
                    tab === 'doctor'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Doctor Workspace
                </button>
                <button
                  type="button"
                  onClick={() => setTab('chemist')}
                  className={`px-3 py-1.5 rounded-lg transition-all font-bold ${
                    tab === 'chemist'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Chemist Workspace
                </button>
                <button
                  type="button"
                  onClick={() => setTab('blood_bank')}
                  className={`px-3 py-1.5 rounded-lg transition-all font-bold ${
                    tab === 'blood_bank'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Blood Bank Workspace
                </button>
                <button
                  type="button"
                  onClick={() => setTab('admin')}
                  className={`px-3 py-1.5 rounded-lg transition-all font-bold ${
                    tab === 'admin'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Admin Workspace
                </button>
              </>
            ) : (
              <span className="px-4 py-1.5 font-bold text-slate-300 uppercase tracking-widest text-[10px]">
                {role === 'doctor' && '🩺 Doctor Dashboard'}
                {role === 'chemist' && '💊 Chemist Dashboard'}
                {role === 'blood_bank' && '🩸 Blood Bank Dashboard'}
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center space-x-1 bg-red-950/20 border border-red-500/10 hover:border-red-500/20 text-red-400 hover:text-red-300 px-3 py-1.5 rounded-xl transition duration-150 font-bold"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      {/* Main workspace container */}
      <main className="flex-1 flex flex-col">
        {/* Enforce role restrictions for rendering the tabs */}
        {tab === 'doctor' && (role === 'doctor' || role === 'admin') && <DoctorDashboard />}
        {tab === 'chemist' && (role === 'chemist' || role === 'admin') && <ChemistDashboard />}
        {tab === 'blood_bank' && (role === 'blood_bank' || role === 'admin') && <BloodBankDashboard />}
        {tab === 'admin' && role === 'admin' && <AdminDashboard />}
      </main>
    </div>
  );
}

export default App;
