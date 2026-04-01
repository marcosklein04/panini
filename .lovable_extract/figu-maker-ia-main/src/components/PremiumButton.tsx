import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'gold';
  size?: 'sm' | 'md' | 'lg';
}

export const PremiumButton = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    const base = 'relative font-display font-bold uppercase tracking-wider rounded-lg transition-all duration-300 overflow-hidden group disabled:opacity-40 disabled:cursor-not-allowed';

    const variants = {
      primary: 'bg-gradient-to-r from-primary to-glow-red text-primary-foreground hover:shadow-[0_0_30px_hsl(var(--primary)/0.4)] hover:scale-105 active:scale-95',
      secondary: 'bg-gradient-to-r from-secondary to-glow-blue text-secondary-foreground hover:shadow-[0_0_30px_hsl(var(--secondary)/0.4)] hover:scale-105 active:scale-95',
      ghost: 'bg-transparent border border-border text-foreground hover:bg-muted hover:border-primary/50 active:scale-95',
      gold: 'bg-gradient-to-r from-gold to-yellow-400 text-gold-foreground hover:shadow-[0_0_40px_hsl(var(--gold)/0.5)] hover:scale-105 active:scale-95',
    };

    const sizes = {
      sm: 'px-4 py-2 text-xs',
      md: 'px-6 py-3 text-sm',
      lg: 'px-8 py-4 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        disabled={disabled}
        {...props}
      >
        {/* Shimmer effect */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{
            background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.15) 45%, rgba(255,255,255,0.25) 50%, rgba(255,255,255,0.15) 55%, transparent 60%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.5s linear infinite',
          }}
        />
        <span className="relative z-10 flex items-center justify-center gap-2">{children}</span>
      </button>
    );
  }
);

PremiumButton.displayName = 'PremiumButton';
