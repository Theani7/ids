const colorMap = {
  green: {
    border: 'border-netgreen/40',
    text: 'text-netgreen',
    glow: '0 0 20px rgba(0,255,136,0.08)',
    bg: 'bg-netgreen/5',
  },
  red: {
    border: 'border-netred/40',
    text: 'text-netred',
    glow: '0 0 20px rgba(255,45,85,0.08)',
    bg: 'bg-netred/5',
  },
  cyan: {
    border: 'border-netcyan/40',
    text: 'text-netcyan',
    glow: '0 0 20px rgba(0,212,255,0.08)',
    bg: 'bg-netcyan/5',
  },
};

export default function StatCard({ title, value, subtitle, color = 'cyan' }) {
  const c = colorMap[color] || colorMap.cyan;

  return (
    <div
      className={`
        relative rounded border ${c.border} ${c.bg} bg-netsurface p-5
        transition-all duration-300 hover:scale-[1.02]
      `}
      style={{ boxShadow: c.glow }}
    >
      <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-2">
        {title}
      </p>
      <p className={`text-3xl font-mono font-bold ${c.text} leading-none mb-1`}>
        {value}
      </p>
      {subtitle && (
        <p className="text-xs font-mono text-[#8b9ab3] mt-1">{subtitle}</p>
      )}
      {/* Accent line */}
      <div className={`absolute bottom-0 left-0 h-[2px] w-full ${c.bg} rounded-b`} />
    </div>
  );
}
