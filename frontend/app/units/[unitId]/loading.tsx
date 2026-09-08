export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="mb-1 h-6 w-56 rounded bg-muted" />
      <div className="mb-5 h-4 w-72 rounded bg-muted" />
      <div className="mb-4 h-40 rounded-lg border border-border bg-card shadow-sm" />
      <div className="h-32 rounded-lg border border-border bg-card shadow-sm" />
    </div>
  );
}
