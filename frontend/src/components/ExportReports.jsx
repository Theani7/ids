import { useState } from 'react';
import { exportCSV, exportJSON, clearHistory } from '../services/api';
import { Download, FileSpreadsheet, FileJson, Trash2, AlertCircle } from 'lucide-react';
import { useToast } from './ui/Toast';

export default function ExportReports() {
  const [days, setDays] = useState(7);
  const [exporting, setExporting] = useState(false);
  const [clearing, setClearing] = useState(false);
  const { addToast } = useToast();

  const handleExportCSV = () => {
    setExporting(true);
    exportCSV(days);
    setTimeout(() => setExporting(false), 1000);
  };

  const handleExportJSON = () => {
    setExporting(true);
    exportJSON(days);
    setTimeout(() => setExporting(false), 1000);
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear ALL monitoring history? This action cannot be undone.')) {
      return;
    }

    setClearing(true);
    try {
      await clearHistory();
      addToast('Monitoring history cleared successfully', 'success');
    } catch (err) {
      console.error('Failed to clear history:', err);
      addToast('Failed to clear history', 'error');
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export Reports
        </h2>

        <div className="border border-netborder bg-netsurface rounded p-4 space-y-4">
          <div>
            <label className="text-xs font-mono uppercase text-[#8b9ab3] block mb-2">
              Time Range
            </label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full bg-netbg border border-netborder text-[#e6edf3] font-mono text-sm rounded px-3 py-2"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleExportCSV}
              disabled={exporting}
              className="flex items-center justify-center gap-2 px-4 py-3 border border-netgreen text-netgreen rounded hover:bg-netgreen hover:text-black transition-all disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span className="text-xs font-mono uppercase">Export CSV</span>
            </button>

            <button
              onClick={handleExportJSON}
              disabled={exporting}
              className="flex items-center justify-center gap-2 px-4 py-3 border border-netcyan text-netcyan rounded hover:bg-netcyan hover:text-black transition-all disabled:opacity-50"
            >
              <FileJson className="w-4 h-4" />
              <span className="text-xs font-mono uppercase">Export JSON</span>
            </button>
          </div>

          <p className="text-xs font-mono text-[#5a6a7a]">
            Downloads will include all alerts from the selected time period with full details.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
          <Trash2 className="w-4 h-4 text-netred" />
          System Maintenance
        </h2>

        <div className="border border-netred/20 bg-netred/5 rounded p-4 space-y-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-netred shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-white mb-1">Clear Monitoring History</h3>
              <p className="text-xs text-[#8b9ab3]">
                Permanently delete all historical alerts, DNS queries, and traffic statistics.
                Use this to reset the system for a new analysis session.
              </p>
            </div>
          </div>

          <button
            onClick={handleClearHistory}
            disabled={clearing}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-netred text-black font-bold rounded hover:bg-red-600 transition-all disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-xs font-mono uppercase">{clearing ? 'Clearing...' : 'Clear All History'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
