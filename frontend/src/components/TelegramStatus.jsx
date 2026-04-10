export default function TelegramStatus({ lastAlert }) {
  const isMalicious = lastAlert?.label === 'MALICIOUS';

  return (
    <div className="border border-netborder bg-netsurface rounded p-4">
      <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
        Telegram Bot
      </h3>

      <div className="flex items-center gap-2 mb-3">
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            isMalicious
              ? 'bg-netred animate-glow-red'
              : 'bg-netgreen animate-pulse'
          }`}
          style={
            isMalicious
              ? { boxShadow: '0 0 6px rgba(255,45,85,0.5)' }
              : { boxShadow: '0 0 6px rgba(0,255,136,0.4)' }
          }
        />
        <span className="text-xs font-mono text-[#e6edf3]">
          📡 TELEGRAM BOT ACTIVE
        </span>
      </div>

      {lastAlert ? (
        <div className="bg-netbg/50 rounded px-3 py-2">
          <p className="text-[10px] font-mono text-[#8b9ab3] mb-1">
            Last notification
          </p>
          <p className="text-xs font-mono text-[#e6edf3]">
            <span
              className={isMalicious ? 'text-netred' : 'text-netgreen'}
            >
              {lastAlert.label}
            </span>{' '}
            —{' '}
            {lastAlert.timestamp
              ? new Date(lastAlert.timestamp).toLocaleTimeString()
              : '--:--:--'}
          </p>
          <p className="text-[10px] font-mono text-netcyan mt-1 truncate">
            {lastAlert.src_ip} → {lastAlert.dst_ip}
          </p>
        </div>
      ) : (
        <p className="text-xs font-mono text-[#8b9ab3]">
          Awaiting first flow...
        </p>
      )}
    </div>
  );
}
