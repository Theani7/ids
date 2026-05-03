export default function StatusBadge({ label }) {
  const isMalicious = label === 'MALICIOUS';

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold tracking-wider
        ${
          isMalicious
            ? 'bg-netred/10 text-netred border border-netred/30'
            : 'bg-netgreen/10 text-netgreen border border-netgreen/30'
        }
      `}
      style={
        isMalicious
          ? { boxShadow: '0 0 8px rgba(255,45,85,0.25)' }
          : {}
      }
    >
      {/* Pulsing dot */}
      <span
        className={`
          inline-block w-1.5 h-1.5 rounded-full
          ${isMalicious ? 'bg-netred animate-pulse-fast' : 'bg-netgreen animate-pulse'}
        `}
      />
      {label}
    </span>
  );
}
