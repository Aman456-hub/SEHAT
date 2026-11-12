import React, { useState } from 'react';
import { api } from '../api/client';
import { Activity, Lock, Phone, Mail, Shield, Loader2 } from 'lucide-react';

/**
 * LoginPage Component
 * Provides a secure entry gate to Doctor, Chemist, and Admin dashboards.
 *
 * @component
 * @param {Object} props
 * @param {function} props.onLoginSuccess - Callback invoked on successful login
 */
export function LoginPage({ onLoginSuccess }) {
  const [role, setRole] = useState('doctor'); // 'doctor', 'chemist', 'admin'
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/auth/login', {
        identifier,
        password,
        role
      });

      if (response.success) {
        const { token, role: userRole, user } = response.data;
        onLoginSuccess(token, userRole, user);
      } else {
        throw new Error(response.message || 'Login failed. Please verify credentials.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 select-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(99,102,241,0.08),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_70%,rgba(16,185,129,0.05),transparent_50%)]" />

      <div className="relative w-full max-w-md bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-3xl p-8 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
        {/* Logo and title */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-4 py-2 rounded-full mb-3">
            <Activity className="h-5 w-5 text-indigo-400 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-widest font-mono">SEHAT Platform</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Access Control Gate</h1>
          <p className="text-slate-400 text-xs mt-1 text-center">
            Sign in to access your secure coordinator dashboard
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div className="grid grid-cols-4 gap-1 bg-slate-950/80 border border-slate-800/60 p-1.5 rounded-2xl mb-6">
          {['doctor', 'chemist', 'blood_bank', 'admin'].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => {
                setRole(r);
                setIdentifier('');
                setError(null);
              }}
              className={`py-2 text-[9px] font-extrabold uppercase tracking-wider rounded-xl transition-all duration-150 ${
                role === r
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {r.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          {/* Identifier Input (Phone or Email) */}
          <div className="space-y-1.5">
            <label className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block">
              {role === 'admin' ? 'Email Address' : 'WhatsApp Phone Number'}
            </label>
            <div className="relative">
              <span className="absolute left-4 top-3.5 text-slate-500">
                {role === 'admin' ? <Mail className="h-4 w-4" /> : <Phone className="h-4 w-4" />}
              </span>
              <input
                type={role === 'admin' ? 'email' : 'text'}
                placeholder={role === 'admin' ? 'admin@sehat.in' : '+919999999999'}
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                className="w-full bg-slate-950/80 border border-slate-800/80 text-white rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:border-indigo-500/80 transition placeholder-slate-600"
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-1.5">
            <label className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block">
              Password
            </label>
            <div className="relative">
              <span className="absolute left-4 top-3.5 text-slate-500">
                <Lock className="h-4 w-4" />
              </span>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-950/80 border border-slate-800/80 text-white rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:border-indigo-500/80 transition placeholder-slate-600"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-700/50 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-xl transition shadow-[0_4px_20px_rgba(99,102,241,0.25)] flex items-center justify-center space-x-2 text-sm"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <Shield className="h-4 w-4" />
                <span>Access Dashboard</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center border-t border-slate-800/40 pt-4 text-[10px] text-slate-600 font-bold uppercase tracking-widest">
          Secured with SHA-256 / JWT Tokens
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
