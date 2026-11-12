import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

/**
 * Custom React hook to manage queue state, doctor availability, and polling.
 * @param {number} doctorId - The ID of the doctor dashboard to monitor.
 */
export function useQueue(doctorId = 1) {
  const [queue, setQueue] = useState([]);
  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch doctor and queue data
  const fetchData = useCallback(async () => {
    try {
      // 1. Fetch Doctor details
      const docRes = await api.get(`/api/doctors/${doctorId}`);
      if (docRes.success) {
        setDoctor(docRes.data);
      } else {
        throw new Error(docRes.message || 'Failed to fetch doctor info.');
      }

      // 2. Fetch Live Queue
      const queueRes = await api.get(`/api/tokens/doctor/${doctorId}`);
      if (queueRes.success) {
        setQueue(queueRes.data);
      } else {
        throw new Error(queueRes.message || 'Failed to fetch active queue.');
      }

      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching dashboard queue:', err);
    } finally {
      setLoading(false);
    }
  }, [doctorId]);

  // Set up polling (every 5 seconds) for real-time queue updates
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Helper to synthesize a premium audio notification chime
  const playChime = () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
      osc1.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1); // A5
      
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(659.25, ctx.currentTime); // E5
      osc2.frequency.exponentialRampToValueAtTime(1046.50, ctx.currentTime + 0.15); // C6
      
      gainNode.gain.setValueAtTime(0.15, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
      
      osc1.connect(gainNode);
      osc2.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      osc1.start();
      osc2.start();
      osc1.stop(ctx.currentTime + 0.6);
      osc2.stop(ctx.currentTime + 0.6);
    } catch (e) {
      console.warn('Audio Context block:', e);
    }
  };

  // Action: Toggle availability
  const toggleAvailability = async (isAvailable) => {
    try {
      const res = await api.patch(`/api/doctors/${doctorId}/availability`, {
        is_available: isAvailable,
      });
      if (res.success) {
        setDoctor(res.data);
        playChime();
        if (!isAvailable) {
          // If toggled offline, active tokens are cancelled by backend. Refresh queue.
          setQueue([]);
        }
      } else {
        alert(`Failed to update status: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed toggling availability:', err);
    }
  };

  // Action: Mark patient as CALLED (takes their turn)
  const callPatient = async (tokenId) => {
    try {
      const res = await api.patch(`/api/tokens/${tokenId}/status`, {
        status: 'called',
      });
      if (res.success) {
        playChime();
        // Optimistic UI updates
        setQueue((prev) =>
          prev.map((t) => (t.id === tokenId ? res.data : t))
        );
        fetchData(); // Trigger fresh fetch to sync queue estimations
      } else {
        alert(`Failed to call patient: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed calling patient:', err);
    }
  };

  // Action: Mark patient as SEEN (completed consultation)
  const seenPatient = async (tokenId) => {
    try {
      const res = await api.patch(`/api/tokens/${tokenId}/status`, {
        status: 'seen',
      });
      if (res.success) {
        playChime();
        fetchData(); // Fetch immediately, as marking seen auto-calls next and reorders queue
      } else {
        alert(`Failed to complete session: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed marking seen:', err);
    }
  };

  // Action: Cancel token (patient absent / left)
  const cancelPatient = async (tokenId) => {
    try {
      const res = await api.patch(`/api/tokens/${tokenId}/status`, {
        status: 'cancelled',
      });
      if (res.success) {
        playChime();
        fetchData(); // Sync queue
      } else {
        alert(`Failed to cancel token: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed cancelling token:', err);
    }
  };

  return {
    queue,
    doctor,
    loading,
    error,
    refreshQueue: fetchData,
    toggleAvailability,
    callPatient,
    seenPatient,
    cancelPatient,
  };
}

export default useQueue;
