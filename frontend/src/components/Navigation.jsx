import { NavLink } from 'react-router-dom';
import { Activity, UploadCloud, ShieldAlert } from 'lucide-react';

export default function Navigation() {
  return (
    <nav className="w-64 bg-netsurface border-r border-netborder flex flex-col h-full">
      {/* Brand */}
      <div className="p-6 border-b border-netborder">
        <div className="flex items-center gap-3 text-netcyan mb-1">
          <ShieldAlert size={28} className="animate-pulse" />
          <h1 className="font-orbitron text-2xl font-bold tracking-wider">
            IntruML
          </h1>
        </div>
        <p className="text-[10px] font-mono text-[#8b9ab3] uppercase tracking-widest pl-10">
          SaaS Edition
        </p>
      </div>

      {/* Links */}
      <div className="flex-1 py-6 flex flex-col gap-2 px-4">
        <NavLink
          to="/live"
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded transition-all duration-200 ${
              isActive
                ? 'bg-netcyan/10 text-netcyan border border-netcyan/30'
                : 'text-[#8b9ab3] hover:bg-netbg hover:text-[#e6edf3]'
            }`
          }
        >
          <Activity size={18} />
          <span className="text-sm tracking-wide">Live Tracker</span>
        </NavLink>

        <NavLink
          to="/batch"
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded transition-all duration-200 ${
              isActive
                ? 'bg-netcyan/10 text-netcyan border border-netcyan/30'
                : 'text-[#8b9ab3] hover:bg-netbg hover:text-[#e6edf3]'
            }`
          }
        >
          <UploadCloud size={18} />
          <span className="text-sm tracking-wide">Batch Analyzer</span>
        </NavLink>
      </div>
    </nav>
  );
}
