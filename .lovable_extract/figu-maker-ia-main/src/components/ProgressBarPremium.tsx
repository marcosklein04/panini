interface Props {
  progress: number;
  currentStep: number;
  totalSteps: number;
}

export function ProgressBarPremium({ progress, currentStep, totalSteps }: Props) {
  return (
    <div className="w-full max-w-md mx-auto space-y-3">
      <div className="flex justify-between items-center text-sm font-body">
        <span className="text-muted-foreground">Paso {currentStep + 1} de {totalSteps}</span>
        <span className="text-muted-foreground font-medium">{Math.round(progress)}%</span>
      </div>
      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, hsl(var(--primary)), hsl(var(--secondary)), hsl(var(--accent)))`,
          }}
        />
        <div
          className="absolute inset-y-0 left-0 rounded-full opacity-60"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)`,
            backgroundSize: '200% 100%',
            animation: 'shimmer 2s linear infinite',
          }}
        />
      </div>
    </div>
  );
}
