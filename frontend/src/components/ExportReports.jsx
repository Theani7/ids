import { useState } from 'react';
import { exportCSV, exportJSON } from '../api/client';
import { Download, FileSpreadsheet, FileJson } from 'lucide-react';

export default function ExportReports() {
  const [days, setDays] = useState(7);
  const [exporting, setExporting] = useState(false);

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

  return (
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
  );
}
