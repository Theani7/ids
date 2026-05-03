export default function SkeletonCard() {
  return (
    <div className="card p-4 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-3 flex-1">
          <div className="h-3 bg-netborder rounded w-24" />
          <div className="h-8 bg-netborder rounded w-32" />
          <div className="h-3 bg-netborder rounded w-40" />
        </div>
        <div className="h-10 w-10 bg-netborder rounded-lg" />
      </div>
    </div>
  );
}
