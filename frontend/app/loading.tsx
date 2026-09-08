export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="mb-5 flex items-center justify-between">
        <div className="h-6 w-24 rounded bg-muted" />
        <div className="h-8 w-32 rounded bg-muted" />
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4 border-b border-border px-4 py-4 last:border-0">
            <div className="h-4 w-28 rounded bg-muted" />
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="h-4 w-16 rounded bg-muted" />
            <div className="h-4 w-20 rounded bg-muted" />
          </div>
        ))}
      </div>
    </div>
  );
}
