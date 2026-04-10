import { NavLink } from 'react-router-dom';
import { Activity, UploadCloud, ShieldAlert, BarChart3, FileCode } from 'lucide-react';

const navItems = [
  { to: '/live', icon: Activity, label: 'Live Tracker' },
  { to: '/batch', icon: UploadCloud, label: 'Batch Analyzer' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/pcap', icon: FileCode, label: 'PCAP Analysis' },
];

export default function Navigation() {
  return (
    <nav className="w-60 bg-netsurface border-r border-netborder flex flex-col h-full">
      {/* Brand */}
      <div className="p-5 border-b border-netborder">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-netcyan/10 rounded-lg">
            <ShieldAlert size={22} className="text-netcyan" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">IntruML</h1>
            <p className="text-xs text-gray-500">IDS Dashboard</p>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="flex-1 py-4 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-netcyan/10 text-netcyan border border-netcyan/30'
                  : 'text-gray-400 hover:bg-netbg hover:text-white'
              }`
            }
          >
            <item.icon size={18} />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-netborder">
        <p className="text-xs text-gray-500 text-center">
          v1.0.0 • XGBoost Powered
        </p>
      </div>
    </nav>
  );
}
