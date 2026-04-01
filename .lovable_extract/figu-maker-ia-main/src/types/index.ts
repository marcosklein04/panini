export interface PlayerData {
  nombre: string;
  apellido: string;
  fechaNacimiento: string;
  altura: string;
  peso: string;
  equipo: string;
}

export interface QuizStep {
  id: keyof PlayerData;
  label: string;
  placeholder: string;
  type: 'text' | 'date' | 'number' | 'select';
  options?: string[];
}

export interface ProcessingStep {
  id: string;
  label: string;
  duration: number;
}

export interface FiguritaResult {
  imageUrl: string;
  playerData: PlayerData;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
