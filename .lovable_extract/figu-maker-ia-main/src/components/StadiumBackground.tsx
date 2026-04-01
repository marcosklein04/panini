import stadiumBg from '@/assets/stadium-bg.jpg';

export function StadiumBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      {/* Stadium photo */}
      <img
        src={stadiumBg}
        alt=""
        className="absolute inset-0 w-full h-full object-cover opacity-30"
        width={1920}
        height={1080}
      />

      {/* Dark overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-background/60" />

      {/* Color accents */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-glow-blue/10 blur-[120px] animate-pulse-glow" />
      <div className="absolute top-1/3 right-1/4 w-80 h-80 rounded-full bg-glow-red/10 blur-[100px] animate-pulse-glow" style={{ animationDelay: '1s' }} />
      <div className="absolute bottom-1/4 left-1/2 w-72 h-72 rounded-full bg-glow-green/8 blur-[100px] animate-pulse-glow" style={{ animationDelay: '2s' }} />

      {/* Floating particles */}
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-foreground/20"
          style={{
            left: `${Math.random() * 100}%`,
            bottom: `-5%`,
            animation: `float-particle ${8 + Math.random() * 12}s linear infinite`,
            animationDelay: `${Math.random() * 10}s`,
          }}
        />
      ))}

      {/* Noise */}
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      }} />
    </div>
  );
}
