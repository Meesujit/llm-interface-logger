export default function StreamingIndicator() {
  return (
    <div className="flex items-center gap-2 px-6 py-2 max-w-3xl mx-auto">
      <div className="flex gap-1">
        <span className="w-1.5 h-1.5 bg-primary-400/60 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
        <span className="w-1.5 h-1.5 bg-primary-400/60 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
        <span className="w-1.5 h-1.5 bg-primary-400/60 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
      </div>
      <span className="text-[11px] text-gray-600">Generating...</span>
    </div>
  );
}
