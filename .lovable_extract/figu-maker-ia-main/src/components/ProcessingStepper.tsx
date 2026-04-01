import { useState, useEffect } from 'react';
import { PROCESSING_STEPS } from '@/mocks/data';
import { AnimatedEntry } from './AnimatedEntry';
import { Check, Loader2 } from 'lucide-react';

interface Props {
  onComplete: () => void;
}

export function ProcessingStepper({ onComplete }: Props) {
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (activeStep >= PROCESSING_STEPS.length) {
      onComplete();
      return;
    }
    const step = PROCESSING_STEPS[activeStep];
    const interval = 50;
    const increments = step.duration / interval;
    let count = 0;

    const timer = setInterval(() => {
      count++;
      const stepProgress = (activeStep / PROCESSING_STEPS.length + (count / increments) / PROCESSING_STEPS.length) * 100;
      setProgress(stepProgress);
      if (count >= increments) {
        clearInterval(timer);
        setActiveStep(s => s + 1);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [activeStep, onComplete]);

  return (
    <div className="w-full max-w-md mx-auto space-y-8">
      {/* Central loader */}
      <div className="flex justify-center">
        <div className="relative w-32 h-32">
          <div className="absolute inset-0 rounded-full border-4 border-muted" />
          <svg className="absolute inset-0 w-full h-full -rotate-90">
            <circle cx="64" cy="64" r="60" fill="none" stroke="url(#grad)" strokeWidth="4" strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 60}`}
              strokeDashoffset={`${2 * Math.PI * 60 * (1 - progress / 100)}`}
              className="transition-all duration-300"
            />
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="hsl(var(--primary))" />
                <stop offset="50%" stopColor="hsl(var(--secondary))" />
                <stop offset="100%" stopColor="hsl(var(--accent))" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-display text-xl font-bold text-gradient-primary">{Math.round(progress)}%</span>
          </div>
          {/* Glow */}
          <div className="absolute inset-0 rounded-full animate-pulse-glow"
            style={{ boxShadow: `0 0 40px hsl(var(--primary)/0.2), 0 0 80px hsl(var(--secondary)/0.1)` }} />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {PROCESSING_STEPS.map((step, i) => (
          <AnimatedEntry key={step.id} delay={i * 200}>
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-500 ${
              i < activeStep ? 'glass border border-accent/30' :
              i === activeStep ? 'glass border border-primary/50 glow-red' :
              'bg-muted/20 border border-transparent'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                i < activeStep ? 'bg-accent text-accent-foreground' :
                i === activeStep ? 'bg-primary text-primary-foreground' :
                'bg-muted text-muted-foreground'
              }`}>
                {i < activeStep ? <Check className="w-4 h-4" /> : i === activeStep ? <Loader2 className="w-4 h-4 animate-spin" /> : <span className="text-xs font-display">{i + 1}</span>}
              </div>
              <span className={`font-body text-sm ${
                i <= activeStep ? 'text-foreground' : 'text-muted-foreground'
              }`}>{step.label}</span>
            </div>
          </AnimatedEntry>
        ))}
      </div>
    </div>
  );
}
