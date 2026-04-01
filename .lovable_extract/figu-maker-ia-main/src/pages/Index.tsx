import { useNavigate } from 'react-router-dom';
import { useQuiz } from '@/hooks/useQuiz';
import { StadiumBackground } from '@/components/StadiumBackground';
import { ProgressBarPremium } from '@/components/ProgressBarPremium';
import { StepInput } from '@/components/StepInput';
import { PremiumButton } from '@/components/PremiumButton';
import { AnimatedEntry } from '@/components/AnimatedEntry';
import { ArrowRight, ArrowLeft, Sparkles, Zap } from 'lucide-react';
import { useState } from 'react';

export default function Index() {
  const navigate = useNavigate();
  const quiz = useQuiz();
  const [started, setStarted] = useState(false);

  const handleQuizComplete = () => {
    // Store data in sessionStorage for next steps
    sessionStorage.setItem('playerData', JSON.stringify(quiz.data));
    navigate('/foto');
  };

  if (quiz.isComplete) {
    handleQuizComplete();
  }

  return (
    <div className="min-h-screen relative">
      <StadiumBackground />

      {!started ? (
        /* Hero */
        <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
          <AnimatedEntry>
            <div className="flex items-center gap-2 mb-4">
              <div className="h-px w-8 bg-gradient-to-r from-transparent to-primary" />
              <span className="font-display text-xs tracking-[0.3em] text-primary uppercase">Fútbol + IA</span>
              <div className="h-px w-8 bg-gradient-to-l from-transparent to-primary" />
            </div>
          </AnimatedEntry>

          <AnimatedEntry delay={150}>
            <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-black text-center leading-tight mb-4">
              <span className="text-gradient-primary">Creá tu</span>
              <br />
              <span className="text-foreground">figurita</span>
              <br />
              <span className="text-gradient-gold">con IA</span>
            </h1>
          </AnimatedEntry>

          <AnimatedEntry delay={300}>
            <p className="font-body text-muted-foreground text-center text-lg md:text-xl max-w-md mb-8">
              Convertite en una figurita futbolera única generada por inteligencia artificial
            </p>
          </AnimatedEntry>

          <AnimatedEntry delay={450}>
            <PremiumButton onClick={() => setStarted(true)} variant="primary" size="lg" className="mb-12">
              <Zap className="w-5 h-5" /> Empezar ahora
            </PremiumButton>
          </AnimatedEntry>

          {/* How it works */}
          <AnimatedEntry delay={600}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
              {[
                { icon: '📋', title: 'Completá tus datos', desc: 'Nombre, equipo y más' },
                { icon: '📸', title: 'Sacate una foto', desc: 'O subí una imagen' },
                { icon: '⚡', title: 'Recibí tu figurita', desc: 'Generada por IA en segundos' },
              ].map((item, i) => (
                <div key={i} className="glass rounded-xl p-5 text-center border border-border hover:border-primary/30 transition-all duration-300 hover:scale-[1.02] group">
                  <div className="text-3xl mb-3 group-hover:scale-110 transition-transform duration-300">{item.icon}</div>
                  <h3 className="font-display text-sm font-bold text-foreground mb-1">{item.title}</h3>
                  <p className="font-body text-xs text-muted-foreground">{item.desc}</p>
                </div>
              ))}
            </div>
          </AnimatedEntry>
        </div>
      ) : (
        /* Quiz */
        <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
          <div className="w-full max-w-lg mx-auto space-y-8">
            <AnimatedEntry>
              <ProgressBarPremium progress={quiz.progress} currentStep={quiz.currentStep} totalSteps={quiz.totalSteps} />
            </AnimatedEntry>

            <div className="min-h-[300px] flex items-center justify-center">
              {quiz.step && (
                <StepInput
                  key={quiz.currentStep}
                  step={quiz.step}
                  value={quiz.currentValue}
                  onChange={quiz.setValue}
                  onSubmit={quiz.next}
                  direction={quiz.direction}
                />
              )}
            </div>

            <div className="flex justify-between items-center">
              <PremiumButton
                onClick={quiz.currentStep === 0 ? () => setStarted(false) : quiz.back}
                variant="ghost"
                size="sm"
              >
                <ArrowLeft className="w-4 h-4" /> Atrás
              </PremiumButton>

              {quiz.step?.type !== 'select' && (
                <PremiumButton onClick={quiz.next} variant="primary" size="md" disabled={!quiz.canAdvance}>
                  Siguiente <ArrowRight className="w-4 h-4" />
                </PremiumButton>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
