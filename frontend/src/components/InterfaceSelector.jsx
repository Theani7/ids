import { useState, useEffect } from 'react';
import { Play, Square, Wifi, AlertCircle } from 'lucide-react';
import { getInterfaces } from '../services/api';

export default function InterfaceSelector({ onStart, onStop, capturing }) {
  const [interfaces, setInterfaces] = useState([]);
  const [selected, setSelected] = useState('');
  const [selectedFriendly, setSelectedFriendly] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const data = await getInterfaces();
        setInterfaces(data);
        if (data.length > 0) {
          setSelected(data[0].raw);
          setSelectedFriendly(data[0].friendly);
        }
      } catch {
        setError('Could not load interfaces');
      }
    })();
  }, []);

  const handleStart = async () => {
    if (!selected) return;
    setLoading(true);
    setError('');
    try {
      await onStart(selected);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to start capture');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await onStop();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to stop capture');
    } finally {
      setLoading(false);
    }
  };

  const handleInterfaceChange = (e) => {
    const selectedInterface = interfaces.find(i => i.raw === e.target.value);
    setSelected(e.target.value);
    setSelectedFriendly(selectedInterface?.friendly || e.target.value);
  };

  return (
    <div className="card p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
        <Wifi className="w-4 h-4 text-netcyan" />
        Network Interface
      </h3>

      <select
        value={selected}
        onChange={handleInterfaceChange}
        disabled={capturing}
        className="input mb-3"
      >
        {interfaces.length === 0 && <option value="">No interfaces found</option>}
        {interfaces.map((iface) => (
          <option key={iface.raw} value={iface.raw}>{iface.friendly}</option>
        ))}
      </select>

      {!capturing ? (
        <button
          onClick={handleStart}
          disabled={loading || !selected}
          className="w-full btn-success flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" />
          {loading ? 'Starting...' : 'Start Capture'}
        </button>
      ) : (
        <button
          onClick={handleStop}
          disabled={loading}
          className="w-full btn-danger flex items-center justify-center gap-2"
        >
          <Square className="w-4 h-4" />
          {loading ? 'Stopping...' : 'Stop Capture'}
        </button>
      )}

      {capturing && (
        <div className="mt-3 flex items-center gap-2 text-sm text-netgreen">
          <span className="w-2 h-2 rounded-full bg-netgreen animate-pulse" />
          Capturing on <span className="font-mono text-netcyan">{selectedFriendly}</span>
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-netred">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  );
}
