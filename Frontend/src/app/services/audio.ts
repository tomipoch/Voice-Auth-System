import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class Audio {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private isRecordingSubject = new BehaviorSubject<boolean>(false);
  private audioDataSubject = new BehaviorSubject<string | null>(null);

  constructor() {}

  // Observable para saber si está grabando
  get isRecording$(): Observable<boolean> {
    return this.isRecordingSubject.asObservable();
  }

  // Observable para obtener datos de audio
  get audioData$(): Observable<string | null> {
    return this.audioDataSubject.asObservable();
  }

  // Inicializar grabación
  async initializeRecording(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000 // Frecuencia de muestreo recomendada para biometría de voz
        } 
      });

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus' // Formato compatible
      });

      this.mediaRecorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      });

      this.mediaRecorder.addEventListener('stop', () => {
        this.processAudioData();
      });

      return true;
    } catch (error) {
      console.error('Error al acceder al micrófono:', error);
      return false;
    }
  }

  // Iniciar grabación
  startRecording(): boolean {
    if (!this.mediaRecorder) {
      console.error('MediaRecorder no inicializado');
      return false;
    }

    if (this.mediaRecorder.state === 'inactive') {
      this.audioChunks = []; // Limpiar chunks anteriores
      this.mediaRecorder.start();
      this.isRecordingSubject.next(true);
      return true;
    }

    return false;
  }

  // Detener grabación
  stopRecording(): boolean {
    if (!this.mediaRecorder) {
      console.error('MediaRecorder no inicializado');
      return false;
    }

    if (this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
      this.isRecordingSubject.next(false);
      
      // Detener todas las pistas de audio
      const stream = this.mediaRecorder.stream;
      stream.getTracks().forEach(track => track.stop());
      
      return true;
    }

    return false;
  }

  // Procesar datos de audio
  private async processAudioData(): Promise<void> {
    if (this.audioChunks.length === 0) {
      console.error('No hay datos de audio para procesar');
      return;
    }

    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
    
    // Convertir a base64
    const base64Audio = await this.blobToBase64(audioBlob);
    this.audioDataSubject.next(base64Audio);
  }

  // Convertir Blob a Base64
  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remover el prefijo "data:audio/webm;base64," para obtener solo el base64
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  // Limpiar datos de audio
  clearAudioData(): void {
    this.audioDataSubject.next(null);
    this.audioChunks = [];
  }

  // Verificar soporte del navegador
  isBrowserSupported(): boolean {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  // Obtener el estado actual de grabación
  get isRecording(): boolean {
    return this.isRecordingSubject.value;
  }

  // Obtener los datos de audio actuales
  get currentAudioData(): string | null {
    return this.audioDataSubject.value;
  }
}
