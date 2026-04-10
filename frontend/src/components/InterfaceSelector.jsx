import { useState, useEffect } from 'react';
import { getInterfaces } from '../api/client';

export default function InterfaceSelector({ onStart, onStop, capturing }) {
  const [interfaces, setInterfaces] = useState([]);
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const ifaces = await getInterfaces();
        setInterfaces(ifaces);
        if (ifaces.length > 0) setSelected(ifaces[0]);
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

  return (
    <div className="border border-netborder bg-netsurface rounded p-4">
      <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
        Network Interface
      </h3>

      {/* Dropdown */}
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        disabled={capturing}
        className="w-full bg-netbg border border-netborder text-[#e6edf3] 
                   font-mono text-sm rounded px-3 py-2 mb-3
                   focus:outline-none focus:border-netcyan/50
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {interfaces.length === 0 && (
          <option value="">No interfaces found</option>
        )}
        {interfaces.map((iface) => (
          <option key={iface} value={iface}>
            {iface}
          </option>
        ))}
      </select>

      {/* Buttons */}
      <div className="flex gap-2">
        {!capturing ? (
          <button
            onClick={handleStart}
            disabled={loading || !selected}
            className="flex-1 px-4 py-2 border border-netgreen text-netgreen text-xs font-mono
                       uppercase tracking-wider rounded
                       hover:bg-netgreen hover:text-black
                       transition-all duration-200
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? '...' : '▶ START CAPTURE'}
          </button>
        ) : (
          <button
            onClick={handleStop}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-netred text-netred text-xs font-mono
                       uppercase tracking-wider rounded
                       hover:bg-netred hover:text-black
                       transition-all duration-200
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? '...' : '■ STOP CAPTURE'}
          </button>
        )}
      </div>

      {/* Status */}
      {capturing && (
        <div className="mt-3 flex items-center gap-2 text-xs font-mono text-netgreen">
          <span className="inline-block w-2 h-2 rounded-full bg-netgreen animate-pulse" />
          Capturing on <span className="text-netcyan">{selected}</span>
        </div>
      )}

      {error && (
        <p className="mt-2 text-xs font-mono text-netred">{error}</p>
      )}
    </div>
  );
}
