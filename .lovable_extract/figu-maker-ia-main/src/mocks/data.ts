import { QuizStep, ProcessingStep } from '@/types';

export const QUIZ_STEPS: QuizStep[] = [
  { id: 'nombre', label: '¿Cuál es tu nombre?', placeholder: 'Ej: Lionel', type: 'text' },
  { id: 'apellido', label: '¿Y tu apellido?', placeholder: 'Ej: Messi', type: 'text' },
  { id: 'fechaNacimiento', label: '¿Cuándo naciste?', placeholder: 'DD/MM/AAAA', type: 'date' },
  { id: 'altura', label: '¿Cuánto medís? (cm)', placeholder: 'Ej: 175', type: 'number' },
  { id: 'peso', label: '¿Cuánto pesás? (kg)', placeholder: 'Ej: 72', type: 'number' },
  {
    id: 'equipo',
    label: '¿De qué equipo sos?',
    placeholder: 'Elegí tu equipo',
    type: 'select',
    options: [
      'Boca Juniors', 'River Plate', 'Racing Club', 'Independiente',
      'San Lorenzo', 'Huracán', 'Vélez Sarsfield', 'Argentinos Juniors',
      'Estudiantes LP', 'Gimnasia LP', 'Newell\'s Old Boys', 'Rosario Central',
      'Talleres', 'Belgrano', 'Colón', 'Unión', 'Banfield', 'Lanús',
      'Defensa y Justicia', 'Godoy Cruz', 'Otro',
    ],
  },
];

export const PROCESSING_STEPS: ProcessingStep[] = [
  { id: 'upload', label: 'Subiendo tu foto...', duration: 1500 },
  { id: 'detect', label: 'Detectando rostro...', duration: 2000 },
  { id: 'analyze', label: 'Analizando encuadre...', duration: 1800 },
  { id: 'generate', label: 'Generando tu figurita...', duration: 2500 },
  { id: 'finish', label: 'Aplicando efectos finales...', duration: 1200 },
];

export const MOCK_FIGURITA_URL = '/placeholder.svg';
