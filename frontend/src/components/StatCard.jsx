const colorMap = {
  green: { icon: 'text-netgreen', bg: 'bg-netgreen/10' },
  red: { icon: 'text-netred', bg: 'bg-netred/10' },
  orange: { icon: 'text-netorange', bg: 'bg-netorange/10' },
  cyan: { icon: 'text-netcyan', bg: 'bg-netcyan/10' },
};

export default function StatCard({ icon: Icon, title, value, subtitle, color = 'cyan' }) {
  const c = colorMap[color] || colorMap.cyan;

  return (
    <div className="card p-4 hover:border-netcyan/30 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{title}</p>
          <p className="text-2xl font-semibold text-white">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg ${c.bg}`}>
            <Icon className={`w-5 h-5 ${c.icon}`} />
          </div>
        )}
      </div>
    </div>
  );
}
