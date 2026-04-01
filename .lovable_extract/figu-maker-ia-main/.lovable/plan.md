## Estructura

### Design System
- Paleta: rojo (#E53935), azul (#1565C0), verde (#2E7D32) + degradados
- Fondo: cancha estilizada con texturas CSS
- Glassmorphism, glow effects, animaciones premium

### Páginas
1. `/` - Hero + cuestionario gamificado (paso a paso animado)
2. `/foto` - Cámara/upload con overlay de encuadre tipo figurita
3. `/procesando` - Loader con pasos animados estilo análisis deportivo
4. `/resultado` - Figurita final con wow effect

### Arquitectura
- `src/types/` - Tipos compartidos
- `src/services/` - Capa API con mocks
- `src/mocks/` - Datos mock
- `src/hooks/` - Hooks custom (useCamera, useQuiz)
- `src/components/` - Componentes reutilizables
- `src/pages/` - 4 páginas principales

### Componentes clave
- HeroSection, QuizCard, ProgressBarPremium
- StepInput, TeamSelector, CameraModule
- FrameOverlay, ImageUploader, ProcessingStepper
- FiguritaCard, PremiumButton, StadiumBackground
