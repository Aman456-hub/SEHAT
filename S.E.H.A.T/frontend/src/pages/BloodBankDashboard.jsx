import React, { useState, useEffect } from 'react';
import { useBloodStock } from '../hooks/useBloodStock';
import { BloodGroupCard } from '../components/BloodGroupCard';
import { BloodStockForm } from '../components/BloodStockForm';
import { api } from '../api/client';
import { ShieldCheck, RefreshCw, Activity, Phone, MapPin, Loader2 } from 'lucide-react';

/**
 * BloodBankDashboard Component
 * Renders the primary dashboard view for blood banks to monitor and adjust group stock.
 *
 * @component
 */
export function BloodBankDashboard() {
  const savedUser = JSON.parse(localStorage.getItem('sehat_user') || '{}');
  const userRole = localStorage.getItem('sehat_role') || 'blood_bank';

  const [activeBankId, setActiveBankId] = useState(savedUser?.id || 1);
  const [bank, setBank] = useState(null);
  const [bankLoading, setBankLoading] = useState(true);
  const [banksList, setBanksList] = useState([]);

  const {
    stocks,
    loading: stockLoading,
    error,
    refreshStocks,
    updateStock
  } = useBloodStock(activeBankId);

  // Fetch all blood banks for Admin dropdown
  useEffect(() => {
    if (userRole === 'admin') {
      async function fetchBanks() {
        const res = await api.get('/api/blood-banks');
        if (res.success) {
          setBanksList(res.data);
        }
      }
      fetchBanks();
    }
  }, [userRole]);

  // Fetch Blood Bank profile details
  useEffect(() => {
    async function loadBank() {
      setBankLoading(true);
      try {
        const res = await api.get(`/api/blood-banks/${activeBankId}`);
        if (res.success) {
          setBank(res.data);
        } else {
          console.warn(`Blood bank profile ${activeBankId} not found.`);
        }
      } catch (err) {
        console.error('Error loading blood bank details:', err);
      } finally {
        setBankLoading(false);
      }
    }
    loadBank();
  }, [activeBankId]);

  if (bankLoading || stockLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-300">
        <Loader2 className="h-10 w-10 text-indigo-500 animate-spin mb-4" />
        <p className="text-sm font-semibold uppercase tracking-wider text-slate-400">Loading Blood Bank Dashboard...</p>
      </div>
    );
  }

  const activeBank = bank || {
    name: 'City Blood Bank',
    address: '10, Indirapuram, Ghaziabad',
    phone: '+917777777777',
    is_open_24hrs: true
  };

  const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'];

  const getStockForGroup = (group) => {
    return stocks.find(s => s.blood_group === group);
  };

  // Compute total units available
  const totalUnits = stocks.reduce((acc, curr) => acc + (curr.units_available || 0), 0);

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 select-none">
      {/* Header section */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-8 border-b border-slate-800/80 mb-8 gap-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-extrabold uppercase tracking-widest">
            <ShieldCheck className="h-4 w-4 text-indigo-400" />
            <span>Blood Bank Workspace {userRole === 'admin' && <span className="text-rose-450 font-bold ml-1.5 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wider">Admin Mode</span>}</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-1">
            {activeBank.name}
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-400 text-xs mt-2">
            <span className="flex items-center">
              <MapPin className="h-3.5 w-3.5 mr-1 text-slate-500" /> {activeBank.address}
            </span>
            <span className="flex items-center">
              <Phone className="h-3.5 w-3.5 mr-1 text-slate-500" /> {activeBank.phone}
            </span>
            <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full text-[10px] font-bold">
              {activeBank.is_open_24hrs ? 'OPEN 24 HOURS' : 'CUSTOM HOURS'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 self-start md:self-center">
          {userRole === 'admin' && banksList.length > 0 && (
            <div className="flex flex-col space-y-1">
              <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">Blood Bank Select</span>
              <select
                value={activeBankId}
                onChange={(e) => setActiveBankId(parseInt(e.target.value, 10))}
                className="bg-slate-900 border border-slate-850 hover:border-slate-800 text-slate-200 text-xs font-bold py-2 px-3 rounded-xl focus:outline-none focus:border-indigo-500/60 transition duration-150 cursor-pointer min-w-[200px]"
              >
                {banksList.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <button
            type="button"
            onClick={refreshStocks}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl transition duration-150 shadow-md shadow-indigo-600/10 h-10"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh Stock</span>
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold px-4 py-3 rounded-xl mb-6">
          Failed to sync inventory: {error}
        </div>
      )}

      {/* Summary Stat Card */}
      <section className="mb-8">
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4 max-w-sm">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Total Blood Units</span>
            <span className="text-2xl font-extrabold text-white mt-0.5 block">{totalUnits} units</span>
          </div>
        </div>
      </section>

      {/* Blood Cards Grid */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          Current Inventory Levels
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {bloodGroups.map((group) => (
            <BloodGroupCard
              key={group}
              group={group}
              stock={getStockForGroup(group)}
            />
          ))}
        </div>
      </section>

      {/* Update Inventory Form Section */}
      <section className="bg-slate-900/20 border border-slate-800/60 rounded-3xl p-6 shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-5">
          Adjust Available Units
        </h2>
        <BloodStockForm
          stocks={stocks}
          onUpdateStock={updateStock}
        />
      </section>
    </div>
  );
}

export default BloodBankDashboard;
