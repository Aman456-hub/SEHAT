import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

/**
 * Custom React hook to manage blood bank stock state and updates.
 * @param {number} bankId - The ID of the blood bank to manage.
 */
export function useBloodStock(bankId = 1) {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current blood stocks
  const fetchStocks = useCallback(async () => {
    try {
      const res = await api.get(`/api/blood-banks/${bankId}/stock`);
      if (res.success) {
        setStocks(res.data);
      } else {
        throw new Error(res.message || 'Failed to fetch blood stock list.');
      }
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching blood stocks:', err);
    } finally {
      setLoading(false);
    }
  }, [bankId]);

  // Load stocks on mount/bankId change
  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  // Update units available for a specific blood group
  const updateStock = async (bloodGroup, units) => {
    try {
      const res = await api.post(`/api/blood-banks/${bankId}/stock`, {
        stocks: [
          {
            blood_group: bloodGroup,
            units_available: parseInt(units, 10) || 0
          }
        ]
      });

      if (res.success) {
        // Refresh local stock state
        await fetchStocks();
      } else {
        alert(`Failed to update stock: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed updating blood stock:', err);
    }
  };

  return {
    stocks,
    loading,
    error,
    refreshStocks: fetchStocks,
    updateStock
  };
}

export default useBloodStock;
