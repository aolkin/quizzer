import { assets } from '$app/paths';

export enum Sound {
  Buzzer = 'buzzer',
  Special = 'special',
  DailyDouble = 'dailydouble',
  Timesup = 'timesup',
  RightAnswer = 'rightanswer',
  IncorrectAnswer = 'incorrectanswer',
}

export class AudioClient {
  private sounds: Map<string, HTMLAudioElement>;

  constructor() {
    this.sounds = new Map();
    this.initializeAudio();
  }

  private initializeAudio() {
    // Preload common game sounds
    const soundFiles: Record<Sound, string> = {
      buzzer: `${assets}/sounds/rightanswer.mp3`,
      special: `${assets}/sounds/dinosaurgrowl.mp3`,
      dailydouble: `${assets}/sounds/dailydouble.mp3`,
      timesup: `${assets}/sounds/timesup.mp3`,
      rightanswer: `${assets}/sounds/rightanswer.mp3`,
      incorrectanswer: `${assets}/sounds/incorrectanswer.mp3`,
    };

    for (const [key, path] of Object.entries(soundFiles)) {
      const audio = new Audio(path);
      audio.preload = 'auto';
      this.sounds.set(key, audio);
    }
  }

  public play(soundName: Sound) {
    const sound = this.sounds.get(soundName);
    if (sound) {
      // Reset and play
      sound.currentTime = 0;
      sound.play().catch((error) => console.error('Error playing sound:', error));
    }
  }

  public setVolume(volume: number) {
    for (const sound of this.sounds.values()) {
      sound.volume = Math.max(0, Math.min(1, volume));
    }
  }

  public dispose() {
    for (const sound of this.sounds.values()) {
      sound.remove();
    }
    this.sounds.clear();
  }
}
