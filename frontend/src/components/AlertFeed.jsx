import StatusBadge from './StatusBadge';

export default function AlertFeed({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="border border-netborder bg-netsurface rounded p-4 h-full flex flex-col">
        <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
          Live Alerts
        </h3>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm font-mono text-[#8b9ab3]">
            No alerts yet — waiting for traffic
            <span className="animate-blink">▌</span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-netborder bg-netsurface rounded p-4 flex flex-col h-full">
      <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
        Live Alerts
        <span className="ml-2 text-netcyan">[{alerts.length}]</span>
      </h3>

      <div className="flex-1 overflow-y-auto space-y-1 pr-1">
        {alerts.map((alert, idx) => {
          const isMalicious = alert.label === 'MALICIOUS';
          const ts = alert.timestamp
            ? new Date(alert.timestamp).toLocaleTimeString()
            : '--:--:--';
          const confidence = ((alert.confidence || 0) * 100).toFixed(1);

          return (
            <div
              key={alert.id || idx}
              className={`
                flex items-center gap-3 px-3 py-2 rounded
                border-l-[3px] bg-netbg/50
                transition-all duration-300
                ${isMalicious ? 'border-l-netred' : 'border-l-netgreen'}
                ${idx === 0 ? 'animate-fade-in' : ''}
              `}
            >
              {/* Timestamp */}
              <span className="text-[10px] font-mono text-[#8b9ab3] shrink-0 w-16">
                {ts}
              </span>

              {/* Flow */}
              <span className="text-xs font-mono text-netcyan truncate min-w-0 flex-1">
                {alert.src_ip}:{alert.src_port}
                <span className="text-[#8b9ab3] mx-1">→</span>
                {alert.dst_ip}:{alert.dst_port}
              </span>

              {/* Protocol */}
              <span className="text-[10px] font-mono px-1.5 py-0.5 bg-netborder/40 text-[#8b9ab3] rounded shrink-0">
                {alert.protocol}
              </span>

              {/* Badge */}
              <StatusBadge label={alert.label} />

              {/* Confidence bar */}
              <div className="w-16 shrink-0">
                <div className="h-1 rounded-full bg-netborder overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isMalicious ? 'bg-netred' : 'bg-netgreen'
                    }`}
                    style={{ width: `${confidence}%` }}
                  />
                </div>
                <p className="text-[9px] font-mono text-[#8b9ab3] text-right mt-0.5">
                  {confidence}%
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
