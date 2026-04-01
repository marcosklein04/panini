import { useRef } from 'react';
import { Camera, Upload, RotateCcw, Check } from 'lucide-react';
import { PremiumButton } from './PremiumButton';
import { AnimatedEntry } from './AnimatedEntry';

interface Props {
  videoRef: React.RefObject<HTMLVideoElement>;
  photo: string | null;
  isCameraActive: boolean;
  error: string | null;
  onStartCamera: () => void;
  onTakePhoto: () => void;
  onFileUpload: (file: File) => void;
  onReset: () => void;
  onConfirm: () => void;
}

export function CameraModule({
  videoRef, photo, isCameraActive, error,
  onStartCamera, onTakePhoto, onFileUpload, onReset, onConfirm
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="w-full max-w-lg mx-auto space-y-6">
      {/* Viewfinder */}
      <AnimatedEntry>
        <div className="relative aspect-[3/4] rounded-2xl overflow-hidden glass border-2 border-border">
          {isCameraActive && (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="absolute inset-0 w-full h-full object-cover"
            />
          )}

          {photo && (
            <img src={photo} alt="Tu foto" className="absolute inset-0 w-full h-full object-cover" />
          )}

          {!isCameraActive && !photo && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-muted-foreground">
              <Camera className="w-16 h-16 opacity-30" />
              <p className="font-body text-sm">Tomá o subí tu foto</p>
            </div>
          )}

          {/* Frame overlay - figurita guide */}
          {(isCameraActive || !photo) && (
            <div className="absolute inset-0 pointer-events-none">
              {/* Corner markers */}
              <div className="absolute top-6 left-6 w-12 h-12 border-t-2 border-l-2 border-primary/70 rounded-tl-lg" />
              <div className="absolute top-6 right-6 w-12 h-12 border-t-2 border-r-2 border-primary/70 rounded-tr-lg" />
              <div className="absolute bottom-6 left-6 w-12 h-12 border-b-2 border-l-2 border-primary/70 rounded-bl-lg" />
              <div className="absolute bottom-6 right-6 w-12 h-12 border-b-2 border-r-2 border-primary/70 rounded-br-lg" />

              {/* Head guide circle */}
              <div className="absolute top-[12%] left-1/2 -translate-x-1/2 w-32 h-32 border-2 border-dashed border-accent/50 rounded-full" />

              {/* Shoulders guide */}
              <div className="absolute top-[42%] left-[15%] right-[15%] h-px border-t border-dashed border-secondary/40" />

              {/* Center line */}
              <div className="absolute top-[5%] bottom-[5%] left-1/2 w-px border-l border-dashed border-foreground/10" />

              {/* Bottom text guide */}
              <div className="absolute bottom-12 left-0 right-0 text-center">
                <span className="text-xs font-body text-foreground/40 bg-background/40 px-3 py-1 rounded-full backdrop-blur-sm">
                  Centrá tu rostro en el círculo
                </span>
              </div>

              {/* Scan line animation */}
              {isCameraActive && (
                <div className="absolute left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-accent/50 to-transparent"
                  style={{ animation: 'scan-line 3s ease-in-out infinite alternate' }}
                />
              )}
            </div>
          )}
        </div>
      </AnimatedEntry>

      {/* Tips */}
      <AnimatedEntry delay={200}>
        <div className="flex flex-wrap gap-2 justify-center">
          {['Centrado', 'Buena luz', 'Mirá al frente', 'Fondo simple'].map((tip) => (
            <span key={tip} className="text-xs font-body px-3 py-1.5 rounded-full glass text-muted-foreground border border-border">
              ✓ {tip}
            </span>
          ))}
        </div>
      </AnimatedEntry>

      {/* Controls */}
      <AnimatedEntry delay={300}>
        <div className="flex gap-3 justify-center">
          {!photo ? (
            <>
              {!isCameraActive ? (
                <>
                  <PremiumButton onClick={onStartCamera} variant="primary" size="lg">
                    <Camera className="w-5 h-5" /> Abrir cámara
                  </PremiumButton>
                  <PremiumButton onClick={() => fileRef.current?.click()} variant="ghost" size="lg">
                    <Upload className="w-5 h-5" /> Subir foto
                  </PremiumButton>
                </>
              ) : (
                <PremiumButton onClick={onTakePhoto} variant="gold" size="lg" className="w-full">
                  <Camera className="w-5 h-5" /> Sacar foto
                </PremiumButton>
              )}
            </>
          ) : (
            <>
              <PremiumButton onClick={onReset} variant="ghost" size="md">
                <RotateCcw className="w-4 h-4" /> Otra vez
              </PremiumButton>
              <PremiumButton onClick={onConfirm} variant="gold" size="lg">
                <Check className="w-5 h-5" /> Confirmar
              </PremiumButton>
            </>
          )}
        </div>
      </AnimatedEntry>

      <input ref={fileRef} type="file" accept="image/*" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFileUpload(f); }}
      />

      {error && (
        <p className="text-center text-sm text-destructive font-body">{error}</p>
      )}
    </div>
  );
}
