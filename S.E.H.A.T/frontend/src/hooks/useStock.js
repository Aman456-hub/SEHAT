import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

/**
 * Custom React hook to manage chemist stock lists, search results, and updates.
 * @param {number} chemistId - The ID of the chemist shop dashboard to monitor.
 */
export function useStock(chemistId = 1) {
  const [stocks, setStocks] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all stocks for the current chemist
  const fetchStocks = useCallback(async () => {
    try {
      const res = await api.get(`/api/chemists/${chemistId}/stock`);
      if (res.success) {
        setStocks(res.data);
      } else {
        throw new Error(res.message || 'Failed to fetch stock list.');
      }
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching chemist stocks:', err);
    } finally {
      setLoading(false);
    }
  }, [chemistId]);

  // Load stocks on init
  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  // Search generic/brand medicines for adding stock
  const searchMedicines = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await api.get(`/api/chemists/medicines/search?q=${encodeURIComponent(query)}`);
      if (res.success) {
        setSearchResults(res.data);
      }
    } catch (err) {
      console.error('Error searching medicines:', err);
    }
  };

  // Toggle stock availability status
  const toggleStock = async (medicineId, isAvailable) => {
    try {
      const res = await api.post(`/api/chemists/${chemistId}/stock`, {
        stocks: [
          {
            medicine_id: medicineId,
            is_available: isAvailable,
          },
        ],
      });

      if (res.success) {
        // Refresh local stocks list from backend response
        await fetchStocks();
      } else {
        alert(`Failed to update stock: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed toggling medicine stock:', err);
    }
  };

  // Add a new medicine to the chemist's stock tracking list
  const addMedicineToStock = async (medicineId) => {
    // Default availability is true when adding to dashboard list
    await toggleStock(medicineId, true);
  };

  return {
    stocks,
    searchResults,
    loading,
    error,
    refreshStocks: fetchStocks,
    searchMedicines,
    toggleStock,
    addMedicineToStock,
    setSearchResults
  };
}

export default useStock;
