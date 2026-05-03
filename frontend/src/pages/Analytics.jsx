import { useState } from 'react';
import { BarChart3, TrendingUp, Globe, Download } from 'lucide-react';
import TrafficCharts from '../components/charts/TrafficCharts';
import AttackTrends from '../components/charts/AttackTrends';
import GeoAttackMap from '../components/GeoAttackMap';
import ExportReports from '../components/ExportReports';

const tabs = [
  { id: 'traffic', label: 'Traffic', icon: BarChart3, desc: 'Bandwidth & protocols' },
  { id: 'trends', label: 'Trends', icon: TrendingUp, desc: 'Attack patterns' },
  { id: 'geo', label: 'Geography', icon: Globe, desc: 'Global distribution' },
  { id: 'export', label: 'Export', icon: Download, desc: 'Download reports' },
];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('traffic');

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="px-6 py-4 border-b border-netborder bg-netsurface/50">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-netcyan" />
          <h1 className="text-lg font-semibold text-white">Analytics Dashboard</h1>
        </div>
      </header>

      {/* Tabs */}
      <div className="px-6 py-3 border-b border-netborder">
        <div className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-netcyan/10 text-netcyan border border-netcyan/30'
                    : 'text-gray-400 hover:bg-netbg hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-4 overflow-y-auto">
        {activeTab === 'traffic' && <TrafficCharts />}
        {activeTab === 'trends' && <AttackTrends />}
        {activeTab === 'geo' && <GeoAttackMap />}
        {activeTab === 'export' && <ExportReports />}
      </div>
    </div>
  );
}
