import { useState, useRef, useCallback, useEffect } from 'react';

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 720 }, height: { ideal: 960 } },
      });
      setStream(mediaStream);
      setIsCameraActive(true);
      setError(null);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch {
      setError('No se pudo acceder a la cámara. Intentá subir una foto.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    stream?.getTracks().forEach(t => t.stop());
    setStream(null);
    setIsCameraActive(false);
  }, [stream]);

  const takePhoto = useCallback(() => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setPhoto(dataUrl);
    canvas.toBlob(blob => {
      if (blob) setFile(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.9);
    stopCamera();
  }, [stopCamera]);

  const handleFileUpload = useCallback((f: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setPhoto(e.target?.result as string);
      setFile(f);
    };
    reader.readAsDataURL(f);
  }, []);

  const reset = useCallback(() => {
    setPhoto(null);
    setFile(null);
  }, []);

  useEffect(() => {
    return () => { stream?.getTracks().forEach(t => t.stop()); };
  }, [stream]);

  return { videoRef, photo, file, isCameraActive, error, startCamera, stopCamera, takePhoto, handleFileUpload, reset };
}
