import { useNavigate } from 'react-router-dom';
import { StadiumBackground } from '@/components/StadiumBackground';
import { FiguritaCard } from '@/components/FiguritaCard';
import { AnimatedEntry } from '@/components/AnimatedEntry';
import { PlayerData } from '@/types';

export default function ResultadoPage() {
  const navigate = useNavigate();

  const stored = sessionStorage.getItem('playerData');
  const photo = sessionStorage.getItem('playerPhoto');
  const playerData: PlayerData = stored ? JSON.parse(stored) : {
    nombre: 'Demo', apellido: 'Jugador', fechaNacimiento: '', altura: '180', peso: '75', equipo: 'Argentina',
  };

  return (
    <div className="min-h-screen relative flex flex-col items-center justify-center px-4 py-12">
      <StadiumBackground />

      <AnimatedEntry>
        <div className="text-center mb-8">
          <h1 className="font-display text-2xl md:text-4xl font-bold mb-2">
            <span className="text-gradient-gold">¡Tu figurita está lista!</span>
          </h1>
          <p className="font-body text-muted-foreground text-sm">
            Una pieza única generada con inteligencia artificial
          </p>
        </div>
      </AnimatedEntry>

      <FiguritaCard
        imageUrl={photo || '/placeholder.svg'}
        playerData={playerData}
        onRestart={() => {
          sessionStorage.clear();
          navigate('/');
        }}
      />
    </div>
  );
}
