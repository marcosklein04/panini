import { useNavigate } from 'react-router-dom';
import { StadiumBackground } from '@/components/StadiumBackground';
import { ProcessingStepper } from '@/components/ProcessingStepper';
import { AnimatedEntry } from '@/components/AnimatedEntry';

export default function ProcesandoPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative flex flex-col items-center justify-center px-4 py-12">
      <StadiumBackground />

      <AnimatedEntry>
        <div className="text-center mb-10">
          <h1 className="font-display text-2xl md:text-4xl font-bold text-gradient-primary mb-2">
            Creando tu figurita
          </h1>
          <p className="font-body text-muted-foreground text-sm">
            La IA está trabajando en tu figurita personalizada
          </p>
        </div>
      </AnimatedEntry>

      <ProcessingStepper onComplete={() => navigate('/resultado')} />
    </div>
  );
}
