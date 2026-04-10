import { useState } from 'react';
import { Menu, X, Activity, UploadCloud, BarChart3, FileCode, Shield } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { to: '/live', icon: Activity, label: 'Live Tracker' },
  { to: '/batch', icon: UploadCloud, label: 'Batch Analyzer' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/pcap', icon: FileCode, label: 'PCAP Analysis' },
];

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-netsurface border-b border-netborder z-40 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-netcyan" />
          <span className="font-bold text-white">IntruML</span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 text-gray-400 hover:text-white"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 top-16 bg-netbg/95 backdrop-blur-md z-30 p-4">
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-netcyan/10 text-netcyan border border-netcyan/30'
                      : 'text-gray-400 hover:bg-netsurface hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </>
  );
}
