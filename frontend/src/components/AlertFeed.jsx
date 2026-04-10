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
          const confidence = ((alert.confidence || 0) * 100).toFixed(0);

          return (
            <div
              key={alert.id || idx}
              className={`flex items-center gap-3 p-3 rounded-lg border-l-4 bg-netbg/50 transition-all ${
                isMalicious 
                  ? 'border-l-netred hover:bg-netred/5' 
                  : 'border-l-netgreen hover:bg-netgreen/5'
              } ${idx === 0 ? 'animate-fade-in' : ''}`}
            >
              <span className="text-xs font-mono text-gray-500 shrink-0">{ts}</span>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-mono text-white">{alert.src_ip}</span>
                  <span className="text-gray-500">→</span>
                  <span className="font-mono text-white truncate">{alert.dst_ip}:{alert.dst_port}</span>
                </div>
              </div>

              <span className={`badge ${isMalicious ? 'badge-danger' : 'badge-success'}`}>
                {isMalicious ? <ShieldAlert className="w-3 h-3 mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
                {alert.label}
              </span>

              <div className="w-12 text-right">
                <span className={`text-xs font-medium ${isMalicious ? 'text-netred' : 'text-netgreen'}`}>
                  {confidence}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
