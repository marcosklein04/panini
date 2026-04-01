import { PlayerData } from '@/types';
import { AnimatedEntry } from './AnimatedEntry';
import { PremiumButton } from './PremiumButton';
import { Download, RefreshCw, Share2, Star } from 'lucide-react';

interface Props {
  imageUrl: string;
  playerData: PlayerData;
  onRestart: () => void;
}

export function FiguritaCard({ imageUrl, playerData, onRestart }: Props) {
  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-lg mx-auto">
      {/* Figurita card */}
      <AnimatedEntry>
        <div className="relative animate-card-reveal">
          {/* Outer glow */}
          <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 blur-2xl animate-pulse-glow" />

          {/* Card */}
          <div className="relative w-72 md:w-80 aspect-[3/4] rounded-2xl overflow-hidden border-2 border-gold/50 glow-gold">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary via-secondary to-accent" />

            {/* Pattern overlay */}
            <div className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px)`,
              }}
            />

            {/* Photo area */}
            <div className="absolute top-8 left-8 right-8 bottom-28 rounded-xl overflow-hidden border border-foreground/10 bg-background/20">
              <img src={imageUrl} alt="Tu figurita" className="w-full h-full object-cover" />
            </div>

            {/* Info strip */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background/90 to-transparent">
              <div className="text-center space-y-1">
                <h3 className="font-display text-lg font-bold text-foreground tracking-wider uppercase">
                  {playerData.apellido || 'Jugador'}
                </h3>
                <p className="font-body text-xs text-muted-foreground">
                  {playerData.nombre} · {playerData.equipo}
                </p>
                <div className="flex justify-center gap-1 pt-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-3 h-3 fill-gold text-gold" />
                  ))}
                </div>
              </div>
            </div>

            {/* Top badge */}
            <div className="absolute top-3 right-3 w-10 h-10 rounded-full bg-gold/90 flex items-center justify-center">
              <span className="font-display text-xs font-black text-gold-foreground">IA</span>
            </div>

            {/* Shimmer sweep */}
            <div className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.08) 45%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.08) 55%, transparent 60%)',
                backgroundSize: '200% 100%',
                animation: 'shimmer 3s ease-in-out infinite',
              }}
            />
          </div>
        </div>
      </AnimatedEntry>

      {/* Stats strip */}
      <AnimatedEntry delay={400}>
        <div className="flex gap-4 justify-center">
          {[
            { label: 'Altura', value: `${playerData.altura || '—'} cm` },
            { label: 'Peso', value: `${playerData.peso || '—'} kg` },
            { label: 'Equipo', value: playerData.equipo || '—' },
          ].map((stat) => (
            <div key={stat.label} className="text-center glass rounded-xl px-4 py-3 border border-border min-w-[80px]">
              <p className="font-display text-xs text-muted-foreground uppercase">{stat.label}</p>
              <p className="font-body text-sm font-bold text-foreground">{stat.value}</p>
            </div>
          ))}
        </div>
      </AnimatedEntry>

      {/* Actions */}
      <AnimatedEntry delay={600}>
        <div className="flex flex-wrap gap-3 justify-center">
          <PremiumButton variant="gold" size="lg">
            <Download className="w-5 h-5" /> Descargar
          </PremiumButton>
          <PremiumButton variant="secondary" size="md">
            <Share2 className="w-4 h-4" /> Compartir
          </PremiumButton>
          <PremiumButton variant="ghost" size="md" onClick={onRestart}>
            <RefreshCw className="w-4 h-4" /> Crear otra
          </PremiumButton>
        </div>
      </AnimatedEntry>
    </div>
  );
}
