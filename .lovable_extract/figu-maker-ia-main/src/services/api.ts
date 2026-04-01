import { PlayerData, FiguritaResult, ApiResponse } from '@/types';
import { MOCK_FIGURITA_URL } from '@/mocks/data';

const SIMULATED_DELAY = 1000;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Capa de servicios preparada para conectar con backend real.
 * Mientras tanto usa mocks.
 */
export const api = {
  async submitPlayerData(data: PlayerData): Promise<ApiResponse<{ id: string }>> {
    await delay(SIMULATED_DELAY);
    return { success: true, data: { id: 'mock-session-' + Date.now() } };
  },

  async uploadPhoto(file: File): Promise<ApiResponse<{ photoUrl: string }>> {
    await delay(SIMULATED_DELAY);
    const url = URL.createObjectURL(file);
    return { success: true, data: { photoUrl: url } };
  },

  async generateFigurita(sessionId: string): Promise<ApiResponse<FiguritaResult>> {
    await delay(SIMULATED_DELAY);
    return {
      success: true,
      data: {
        imageUrl: MOCK_FIGURITA_URL,
        playerData: {
          nombre: 'Demo',
          apellido: 'Jugador',
          fechaNacimiento: '1990-01-01',
          altura: '180',
          peso: '75',
          equipo: 'Argentina',
        },
      },
    };
  },

  async checkProcessingStatus(sessionId: string): Promise<ApiResponse<{ progress: number; step: string }>> {
    await delay(500);
    return { success: true, data: { progress: 100, step: 'complete' } };
  },
};
