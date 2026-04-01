import { useState, useCallback } from 'react';
import { PlayerData } from '@/types';
import { QUIZ_STEPS } from '@/mocks/data';

const initialData: PlayerData = {
  nombre: '',
  apellido: '',
  fechaNacimiento: '',
  altura: '',
  peso: '',
  equipo: '',
};

export function useQuiz() {
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<PlayerData>(initialData);
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward');

  const totalSteps = QUIZ_STEPS.length;
  const step = QUIZ_STEPS[currentStep];
  const progress = ((currentStep) / totalSteps) * 100;
  const isComplete = currentStep >= totalSteps;

  const setValue = useCallback((value: string) => {
    setData(prev => ({ ...prev, [step.id]: value }));
  }, [step]);

  const currentValue = data[step?.id] || '';

  const canAdvance = currentValue.trim().length > 0;

  const next = useCallback(() => {
    if (canAdvance && currentStep < totalSteps) {
      setDirection('forward');
      setCurrentStep(s => s + 1);
    }
  }, [canAdvance, currentStep, totalSteps]);

  const back = useCallback(() => {
    if (currentStep > 0) {
      setDirection('backward');
      setCurrentStep(s => s - 1);
    }
  }, [currentStep]);

  return { currentStep, step, data, progress, isComplete, setValue, currentValue, canAdvance, next, back, totalSteps, direction };
}
