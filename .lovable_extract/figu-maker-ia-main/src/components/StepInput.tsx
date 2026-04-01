import { QuizStep } from '@/types';
import { cn } from '@/lib/utils';

interface Props {
  step: QuizStep;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  direction: 'forward' | 'backward';
}

export function StepInput({ step, value, onChange, onSubmit, direction }: Props) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim()) onSubmit();
  };

  if (step.type === 'select' && step.options) {
    return (
      <div className="animate-slide-up-fade space-y-4">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-center text-gradient-primary">
          {step.label}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-[50vh] overflow-y-auto p-1">
          {step.options.map((option) => (
            <button
              key={option}
              onClick={() => { onChange(option); setTimeout(onSubmit, 300); }}
              className={cn(
                'px-4 py-3 rounded-lg text-sm font-body font-medium transition-all duration-300 border',
                value === option
                  ? 'bg-primary/20 border-primary text-primary-foreground glow-red scale-105'
                  : 'glass border-border hover:border-primary/50 hover:bg-primary/10 text-foreground hover:scale-[1.02]'
              )}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up-fade space-y-6 w-full max-w-md mx-auto">
      <h2 className="text-2xl md:text-3xl font-display font-bold text-center text-gradient-primary">
        {step.label}
      </h2>
      <div className="relative group">
        <input
          type={step.type === 'date' ? 'date' : step.type === 'number' ? 'number' : 'text'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={step.placeholder}
          autoFocus
          className={cn(
            'w-full px-6 py-4 rounded-xl text-lg font-body text-center',
            'glass border-2 border-border',
            'focus:outline-none focus:border-primary/60 focus:glow-red',
            'transition-all duration-300',
            'placeholder:text-muted-foreground/50',
            'text-foreground bg-muted/30'
          )}
        />
        <div className="absolute inset-0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, hsl(var(--primary)/0.1), hsl(var(--secondary)/0.1))',
          }}
        />
      </div>
    </div>
  );
}
