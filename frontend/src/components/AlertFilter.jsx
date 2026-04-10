import { Search, Filter, X } from 'lucide-react';
import { useState } from 'react';

export default function AlertFilter({ onFilter, filters }) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState(filters.search || '');
  const [label, setLabel] = useState(filters.label || 'all');

  const handleApply = () => {
    onFilter({ search, label });
    setIsOpen(false);
  };

  const handleClear = () => {
    setSearch('');
    setLabel('all');
    onFilter({ search: '', label: 'all' });
  };

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search IP, port..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 pr-4 py-2 bg-netbg border border-netborder rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-netcyan"
        />
      </div>
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`p-2 rounded-lg border transition-all ${
          isOpen || label !== 'all'
            ? 'bg-netcyan/10 border-netcyan text-netcyan'
            : 'bg-netbg border-netborder text-gray-400 hover:text-white'
        }`}
      >
        <Filter className="w-4 h-4" />
      </button>

      {(search || label !== 'all') && (
        <button
          onClick={handleClear}
          className="p-2 text-gray-400 hover:text-netred transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 p-4 bg-netsurface border border-netborder rounded-lg shadow-xl z-10 min-w-[200px]">
          <label className="block text-sm text-gray-400 mb-2">Status</label>
          <select
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full mb-4 px-3 py-2 bg-netbg border border-netborder rounded text-sm text-white"
          >
            <option value="all">All</option>
            <option value="MALICIOUS">Malicious</option>
            <option value="NORMAL">Normal</option>
          </select>
          <button
            onClick={handleApply}
            className="w-full py-2 bg-netcyan text-netbg font-medium rounded hover:bg-netcyan-light transition-colors"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
