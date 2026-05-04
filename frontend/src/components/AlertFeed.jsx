import { Shield, ShieldAlert } from 'lucide-react';

export default function AlertFeed({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="card p-4 h-full flex flex-col">
        <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
          <Shield className="w-4 h-4 text-netcyan" />
          Live Alerts
        </h3>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-gray-500">
            No alerts yet — waiting for traffic
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-4 flex flex-col h-full">
      <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
        <Shield className="w-4 h-4 text-netcyan" />
        Live Alerts
        <span className="ml-auto text-xs text-gray-500">{alerts.length} total</span>
      </h3>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {alerts.map((alert, idx) => {
          const isMalicious = alert.label === 'MALICIOUS';
          const ts = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : '--:--';
          const confidence = alert.confidence || 0;
          const confidencePct = (confidence * 100).toFixed(0);

          // Determine severity for malicious alerts
          let severity = { label: 'BENIGN', class: 'badge-success', border: 'border-l-netgreen' };
          if (isMalicious) {
            if (confidence >= 0.95) {
              severity = { label: 'CRITICAL', class: 'bg-red-900/40 text-red-400 border-red-500', border: 'border-l-red-600' };
            } else if (confidence >= 0.8) {
              severity = { label: 'HIGH', class: 'bg-orange-900/40 text-orange-400 border-orange-500', border: 'border-l-orange-600' };
            } else if (confidence >= 0.6) {
              severity = { label: 'MEDIUM', class: 'bg-yellow-900/40 text-yellow-400 border-yellow-500', border: 'border-l-yellow-600' };
            } else {
              severity = { label: 'LOW', class: 'bg-blue-900/40 text-blue-400 border-blue-500', border: 'border-l-blue-600' };
            }
          }

          return (
            <div
              key={alert.id || idx}
              className={`flex items-center gap-3 p-3 rounded-lg border-l-4 bg-netbg/50 transition-all ${
                severity.border
              } ${idx === 0 ? 'animate-fade-in' : ''} hover:bg-white/5`}
            >
              <span className="text-xs font-mono text-gray-500 shrink-0">{ts}</span>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-mono text-white">{alert.src_ip}</span>
                  <span className="text-gray-500">→</span>
                  <span className="font-mono text-white truncate">{alert.dst_ip}:{alert.dst_port}</span>
                </div>
                {alert.attack_type && (
                  <div className="text-[10px] font-mono uppercase text-gray-500 mt-1">
                    Pattern: <span className="text-netcyan">{alert.attack_type}</span>
                  </div>
                )}
              </div>

              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${severity.class}`}>
                {severity.label}
              </span>

              <div className="w-12 text-right">
                <span className={`text-xs font-mono font-medium ${isMalicious ? 'text-netred' : 'text-netgreen'}`}>
                  {confidencePct}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
