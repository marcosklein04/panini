import { useNavigate } from 'react-router-dom';
import { useCamera } from '@/hooks/useCamera';
import { StadiumBackground } from '@/components/StadiumBackground';
import { CameraModule } from '@/components/CameraModule';
import { AnimatedEntry } from '@/components/AnimatedEntry';

export default function FotoPage() {
  const navigate = useNavigate();
  const camera = useCamera();

  const handleConfirm = () => {
    if (camera.photo) {
      sessionStorage.setItem('playerPhoto', camera.photo);
      navigate('/procesando');
    }
  };

  return (
    <div className="min-h-screen relative flex flex-col items-center justify-center px-4 py-8">
      <StadiumBackground />

      <AnimatedEntry>
        <div className="text-center mb-6">
          <h1 className="font-display text-2xl md:text-4xl font-bold text-gradient-primary mb-2">
            Tu mejor foto
          </h1>
          <p className="font-body text-muted-foreground text-sm md:text-base">
            Sacate una foto o subí una imagen para tu figurita
          </p>
        </div>
      </AnimatedEntry>

      <CameraModule
        videoRef={camera.videoRef as React.RefObject<HTMLVideoElement>}
        photo={camera.photo}
        isCameraActive={camera.isCameraActive}
        error={camera.error}
        onStartCamera={camera.startCamera}
        onTakePhoto={camera.takePhoto}
        onFileUpload={camera.handleFileUpload}
        onReset={camera.reset}
        onConfirm={handleConfirm}
      />
    </div>
  );
}
