import { Link } from 'react-router-dom';
import { ArrowRight, Activity, Shield, Globe, FileSearch } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0d1117]/80 backdrop-blur-md border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-lg font-semibold tracking-tight">IntruML</span>
          <Link 
            to="/live" 
            className="text-sm text-white/60 hover:text-white transition-colors"
          >
            Dashboard →
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="min-h-screen flex items-center pt-20">
        <div className="max-w-6xl mx-auto px-6 w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Content */}
            <div>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
                Network
                <span className="text-[#58a6ff]"> Security</span>
                <br />
                Intelligence
              </h1>
              <p className="text-lg text-white/60 mb-8 max-w-md leading-relaxed">
                Real-time intrusion detection powered by machine learning. 
                Monitor traffic, detect threats, and protect your infrastructure.
              </p>
              <div className="flex flex-wrap items-center gap-4">
                <Link
                  to="/live"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#58a6ff] text-black font-medium rounded-lg hover:bg-[#79b8ff] transition-colors"
                >
                  <Activity className="w-4 h-4" />
                  Start Monitoring
                </Link>
                <Link
                  to="/batch"
                  className="inline-flex items-center gap-2 px-6 py-3 border border-white/20 rounded-lg hover:border-white/40 hover:bg-white/5 transition-all"
                >
                  <FileSearch className="w-4 h-4" />
                  Analyze PCAP
                </Link>
              </div>
            </div>

            {/* Right: Visual */}
            <div className="relative hidden lg:block">
              <div className="absolute inset-0 bg-[#58a6ff]/20 blur-[100px] rounded-full" />
              <div className="relative bg-[#161b22] border border-white/10 rounded-2xl p-6 shadow-2xl">
                <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                    <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                    <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                  </div>
                  <span className="ml-4 text-xs text-white/40 font-mono">Live Traffic</span>
                </div>
                <div className="space-y-2 font-mono text-sm">
                  <div className="flex items-center gap-3 text-white/60">
                    <span className="text-white/30">12:34:56</span>
                    <span className="text-[#7ee787]">192.168.1.10</span>
                    <span className="text-white/30">→</span>
                    <span>142.250.80.46:443</span>
                    <span className="ml-auto px-2 py-0.5 bg-[#7ee787]/10 text-[#7ee787] rounded text-xs">NORMAL</span>
                  </div>
                  <div className="flex items-center gap-3 text-white/60">
                    <span className="text-white/30">12:34:57</span>
                    <span className="text-[#7ee787]">10.0.0.15</span>
                    <span className="text-white/30">→</span>
                    <span>192.168.1.5:22</span>
                    <span className="ml-auto px-2 py-0.5 bg-[#ff7b72]/10 text-[#ff7b72] rounded text-xs">ALERT</span>
                  </div>
                  <div className="flex items-center gap-3 text-white/60">
                    <span className="text-white/30">12:34:58</span>
                    <span className="text-[#7ee787]">172.16.0.8</span>
                    <span className="text-white/30">→</span>
                    <span>8.8.8.8:53</span>
                    <span className="ml-auto px-2 py-0.5 bg-[#7ee787]/10 text-[#7ee787] rounded text-xs">NORMAL</span>
                  </div>
                  <div className="flex items-center gap-3 text-white/60 animate-pulse">
                    <span className="text-white/30">12:34:59</span>
                    <span className="text-[#ffa657]">45.33.32.156</span>
                    <span className="text-white/30">→</span>
                    <span>192.168.1.1:80</span>
                    <span className="ml-auto px-2 py-0.5 bg-[#ff7b72]/10 text-[#ff7b72] rounded text-xs">THREAT</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 border-y border-white/5 bg-[#161b22]/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-white mb-1">99.9%</div>
              <div className="text-sm text-white/50">Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white mb-1">&lt;10ms</div>
              <div className="text-sm text-white/50">Latency</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white mb-1">24/7</div>
              <div className="text-sm text-white/50">Protection</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12">Key Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Activity, title: 'Live Capture', desc: 'Real-time packet analysis' },
              { icon: Shield, title: 'Threat Detection', desc: 'ML-powered alerts' },
              { icon: FileSearch, title: 'PCAP Analysis', desc: 'Import and analyze' },
              { icon: Globe, title: 'Geolocation', desc: 'Track attack sources' },
            ].map((f, i) => (
              <div key={i} className="p-6 rounded-xl border border-white/10 hover:border-[#58a6ff]/50 hover:bg-[#58a6ff]/5 transition-all group">
                <f.icon className="w-6 h-6 text-[#58a6ff] mb-4 group-hover:scale-110 transition-transform" />
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-white/50">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-white/60 mb-8">Launch the dashboard and start monitoring your network.</p>
          <Link
            to="/live"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-black font-medium rounded-lg hover:bg-white/90 transition-colors"
          >
            Launch Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-white/40">
          <span>IntruML</span>
          <span>© 2024</span>
        </div>
      </footer>
    </div>
  );
}
