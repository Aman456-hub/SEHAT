import React, { useState, useEffect } from 'react';
import { useStock } from '../hooks/useStock';
import { MedicineSearch } from '../components/MedicineSearch';
import { StockToggle } from '../components/StockToggle';
import { api } from '../api/client';
import { Plus, Pill, AlertCircle, RefreshCw, Layers, CheckCircle2, HelpCircle } from 'lucide-react';

/**
 * ChemistDashboard Page Component
 * Renders the chemist dashboard to manage medicine inventory stocks.
 * Includes inventory stats, autocomplete additions, and a grid of stock toggles.
 *
 * @component
 */
export function ChemistDashboard() {
  const savedUser = JSON.parse(localStorage.getItem('sehat_user') || '{}');
  const userRole = localStorage.getItem('sehat_role') || 'chemist';

  const [activeChemistId, setActiveChemistId] = useState(savedUser?.id || 1);
  const [chemist, setChemist] = useState(null);
  const [chemistLoading, setChemistLoading] = useState(true);
  const [chemistsList, setChemistsList] = useState([]);
  
  // Use Chemist ID dynamically from authenticated session
  const {
    stocks,
    searchResults,
    loading: stockLoading,
    error,
    searchMedicines,
    toggleStock,
    addMedicineToStock,
    setSearchResults,
  } = useStock(activeChemistId);

  // Fetch all chemists for Admin dropdown
  useEffect(() => {
    if (userRole === 'admin') {
      async function fetchChemists() {
        const res = await api.get('/api/chemists');
        if (res.success) {
          setChemistsList(res.data);
        }
      }
      fetchChemists();
    }
  }, [userRole]);

  // Fetch chemist metadata
  useEffect(() => {
    async function loadChemist() {
      setChemistLoading(true);
      try {
        const res = await api.get(`/api/chemists/${activeChemistId}`); // Fetch chemist info
        if (res.success) {
          setChemist(res.data);
        } else {
          console.warn('Chemist not found.');
        }
      } catch (err) {
        console.error('Error loading chemist info:', err);
      } finally {
        setChemistLoading(false);
      }
    }
    loadChemist();
  }, [activeChemistId]);

  const totalStocks = stocks.length;
  const inStockCount = stocks.filter((s) => s.is_available).length;
  const outOfStockCount = totalStocks - inStockCount;

  // Stale check: count items not updated in 24 hours
  const staleCount = stocks.filter((s) => {
    const last = new Date(s.last_updated);
    const now = new Date();
    return (now - last) / (1000 * 60 * 60) >= 24;
  }).length;

  const handleSearchClear = () => {
    setSearchResults([]);
  };

  const isLoading = chemistLoading || stockLoading;

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-300">
        <RefreshCw className="h-10 w-10 text-indigo-500 animate-spin mb-4" />
        <p className="text-sm font-semibold uppercase tracking-wider text-slate-400">Loading Chemist Inventory...</p>
      </div>
    );
  }

  // Graceful fallback profile if db seed has not run yet
  const activeChemist = chemist || {
    name: "Mohan Kumar",
    shop_name: "Mohan Chemists & Druggists",
    phone: "+918888888888",
    address: "24, Sector 4, Ghaziabad"
  };

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
      {/* Header Panel */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-slate-800/80 mb-8">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-extrabold uppercase tracking-widest">
            <Pill className="h-4 w-4 animate-pulse" />
            <span>SEHAT Stock Management {userRole === 'admin' && <span className="text-rose-450 font-bold ml-1.5 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wider">Admin Mode</span>}</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-1">
            {activeChemist.shop_name}
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Chemist: {activeChemist.name} • {activeChemist.address}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {userRole === 'admin' && chemistsList.length > 0 && (
            <div className="flex flex-col space-y-1">
              <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">Chemist Workspace Select</span>
              <select
                value={activeChemistId}
                onChange={(e) => setActiveChemistId(parseInt(e.target.value, 10))}
                className="bg-slate-900 border border-slate-850 hover:border-slate-800 text-slate-200 text-xs font-bold py-2 px-3 rounded-xl focus:outline-none focus:border-indigo-500/60 transition duration-150 cursor-pointer min-w-[200px]"
              >
                {chemistsList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.shop_name} ({c.name})
                  </option>
                ))}
              </select>
            </div>
          )}
          {/* Medicine Search Autocomplete */}
          <div className="w-full md:w-auto">
            <MedicineSearch
              results={searchResults}
              onSearch={searchMedicines}
              onSelect={addMedicineToStock}
              onClear={handleSearchClear}
            />
          </div>
        </div>
      </header>

      {/* Stats Cards Section */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4">
          <div className="p-3 bg-slate-800 border border-slate-700/60 text-indigo-400 rounded-xl">
            <Layers className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Total Tracked</span>
            <span className="text-2xl font-extrabold text-white mt-0.5 block">{totalStocks} meds</span>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">In Stock</span>
            <span className="text-2xl font-extrabold text-white mt-0.5 block">{inStockCount} meds</span>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4">
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Out of Stock</span>
            <span className="text-2xl font-extrabold text-white mt-0.5 block">{outOfStockCount} meds</span>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-5 flex items-center space-x-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Stale Items</span>
            <span className="text-2xl font-extrabold text-white mt-0.5 block">{staleCount} warnings</span>
          </div>
        </div>
      </section>

      {/* Inventory Grid Board */}
      <main className="bg-slate-900/20 backdrop-blur-md border border-slate-800/60 rounded-3xl p-6 shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Layers className="h-5 w-5 text-indigo-500" /> Stock Catalog
        </h2>

        {stocks.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-850 rounded-2xl">
            <HelpCircle className="h-10 w-10 text-slate-600 mb-3" />
            <h3 className="text-base font-semibold text-slate-450">No Stock Tracked Yet</h3>
            <p className="text-xs text-slate-500 max-w-xs mt-1">
              Use the search bar in the top right header to look up medicines and add them to your tracking dashboard.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {stocks.map((item) => (
              <StockToggle
                key={item.id}
                stockItem={item}
                onToggle={toggleStock}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ChemistDashboard;
