import { Link } from 'react-router-dom';
import { Shield, Zap, Lock, Database } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-netbg flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-netcyan/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 text-center max-w-4xl px-6">
        <div className="inline-flex items-center justify-center gap-4 mb-6">
          <Shield size={48} className="text-netcyan animate-pulse" />
          <h1 className="text-6xl md:text-8xl font-orbitron font-bold text-transparent bg-clip-text bg-gradient-to-r from-netcyan to-netgreen">
            IntruML
          </h1>
        </div>
        
        <p className="text-xl md:text-2xl text-[#8b9ab3] mb-12 font-mono tracking-wide max-w-2xl mx-auto">
          Next-Generation AI Intrusion Detection. Protect your infrastructure with XGBoost-powered precision.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-20">
          <Link
            to="/live"
            className="px-8 py-4 bg-netcyan/10 border border-netcyan text-netcyan text-sm font-bold uppercase tracking-[0.2em] hover:bg-netcyan hover:text-netbg transition-all duration-300 rounded shadow-[0_0_20px_rgba(0,212,255,0.3)] w-full sm:w-auto"
          >
            Start Monitoring
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-netsurface border border-netborder rounded-lg p-6 text-left hover:scale-[1.02] transition-transform">
            <Zap className="text-netcyan mb-4" size={32} />
            <h3 className="text-lg font-orbitron mb-2">Real-Time Tracker</h3>
            <p className="text-sm text-[#8b9ab3]">Monitor live network interfaces instantly with our blazing fast Scapy integration.</p>
          </div>
          <div className="bg-netsurface border border-netborder rounded-lg p-6 text-left hover:scale-[1.02] transition-transform">
            <Database className="text-netgreen mb-4" size={32} />
            <h3 className="text-lg font-orbitron mb-2">Batch Analysis</h3>
            <p className="text-sm text-[#8b9ab3]">Upload historical PCAP CSVs. Our model processes millions of rows in seconds.</p>
          </div>
          <div className="bg-netsurface border border-netborder rounded-lg p-6 text-left hover:scale-[1.02] transition-transform">
            <Lock className="text-netred mb-4" size={32} />
            <h3 className="text-lg font-orbitron mb-2">99.9% Accuracy</h3>
            <p className="text-sm text-[#8b9ab3]">Trained on the CIC-IDS2017 dataset, IntruML catches DoS, PortScans, and Web Attacks.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
