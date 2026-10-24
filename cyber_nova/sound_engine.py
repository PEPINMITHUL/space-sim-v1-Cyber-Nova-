"""
Procedural Retro Audio Synthesizer and Manager.
Generates 16-bit PCM sound effects using pure standard library math & wave,
then plays them asynchronously with zero latency via Windows sound subsystem.
"""

import os
import math
import struct
import wave
import random
import threading
from pathlib import Path
from config import SOUNDS_DIR, AUDIO_SAMPLE_RATE, DEFAULT_AUDIO_ENABLED

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundEngine:
    def __init__(self, sounds_dir: Path = SOUNDS_DIR):
        self.sounds_dir = Path(sounds_dir)
        self.enabled = HAS_WINSOUND and DEFAULT_AUDIO_ENABLED
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        self._sound_queue = []
        self._lock = threading.Lock()
        
        # Initialize synthesized sounds
        self._ensure_sound_assets()

    def toggle_sound(self) -> bool:
        """Toggle mute state and return new state."""
        self.enabled = not self.enabled
        return self.enabled

    def _write_wav(self, filename: str, samples: list[float], sample_rate: int = AUDIO_SAMPLE_RATE):
        """Write floating-point samples (-1.0 to 1.0) into a 16-bit mono WAV file."""
        filepath = self.sounds_dir / filename
        with wave.open(str(filepath), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # Pack samples into signed 16-bit integers
            packed_frames = bytearray()
            for s in samples:
                val = max(-1.0, min(1.0, s))
                int_val = int(val * 32767.0)
                packed_frames.extend(struct.pack('<h', int_val))
            
            wav_file.writeframes(packed_frames)
        self._cache[filename] = str(filepath)

    def _ensure_sound_assets(self):
        """Synthesize sound assets if they do not already exist."""
        rate = AUDIO_SAMPLE_RATE

        # 1. Laser pew (single shot)
        laser_file = "laser.wav"
        if not (self.sounds_dir / laser_file).exists():
            duration = 0.12
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 950 * math.exp(-3.8 * t)  # exponential pitch drop
                amp = (1.0 - t) * 0.4
                samples.append(amp * math.sin(2 * math.pi * freq * (i / rate)))
            self._write_wav(laser_file, samples)
        else:
            self._cache[laser_file] = str(self.sounds_dir / laser_file)

        # 2. Plasma blast (heavy punch)
        plasma_file = "plasma.wav"
        if not (self.sounds_dir / plasma_file).exists():
            duration = 0.16
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 600 * math.exp(-4.2 * t)
                amp = (1.0 - t ** 0.8) * 0.45
                s = math.sin(2 * math.pi * freq * (i / rate))
                # Add harmonic
                s += 0.3 * math.sin(2 * math.pi * freq * 2.0 * (i / rate))
                samples.append(amp * s)
            self._write_wav(plasma_file, samples)
        else:
            self._cache[plasma_file] = str(self.sounds_dir / plasma_file)

        # 3. Flak shotgun blast
        flak_file = "shotgun.wav"
        if not (self.sounds_dir / flak_file).exists():
            duration = 0.18
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 480 * math.exp(-4.5 * t)
                noise = (random.random() * 2.0 - 1.0) * 0.4
                amp = (1.0 - t) * 0.5
                tone = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * (tone * 0.6 + noise))
            self._write_wav(flak_file, samples)
        else:
            self._cache[flak_file] = str(self.sounds_dir / flak_file)

        # 4. Missile launch
        missile_file = "missile.wav"
        if not (self.sounds_dir / missile_file).exists():
            duration = 0.22
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 300 + 400 * t
                amp = math.sin(math.pi * t) * 0.4
                s = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * s)
            self._write_wav(missile_file, samples)
        else:
            self._cache[missile_file] = str(self.sounds_dir / missile_file)

        # 5. Small explosion
        exp_sm_file = "explosion_sm.wav"
        if not (self.sounds_dir / exp_sm_file).exists():
            duration = 0.25
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                amp = (1.0 - t) ** 1.8 * 0.45
                noise = (random.random() * 2.0 - 1.0)
                freq = 200 * (1.0 - t * 0.8)
                sub = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * (noise * 0.6 + sub * 0.4))
            self._write_wav(exp_sm_file, samples)
        else:
            self._cache[exp_sm_file] = str(self.sounds_dir / exp_sm_file)

        # 6. Big boss explosion
        exp_lg_file = "explosion_lg.wav"
        if not (self.sounds_dir / exp_lg_file).exists():
            duration = 0.65
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                amp = (1.0 - t) ** 1.4 * 0.55
                noise = (random.random() * 2.0 - 1.0)
                sub_freq = 110 * math.exp(-1.5 * t)
                sub = math.sin(2 * math.pi * sub_freq * (i / rate))
                samples.append(amp * (noise * 0.5 + sub * 0.5))
            self._write_wav(exp_lg_file, samples)
        else:
            self._cache[exp_lg_file] = str(self.sounds_dir / exp_lg_file)

        # 7. Shield ping
        shield_file = "shield_hit.wav"
        if not (self.sounds_dir / shield_file).exists():
            duration = 0.15
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                amp = (1.0 - t) ** 2 * 0.4
                s = math.sin(2 * math.pi * 1280 * (i / rate)) + 0.3 * math.sin(2 * math.pi * 1920 * (i / rate))
                samples.append(amp * s * 0.5)
            self._write_wav(shield_file, samples)
        else:
            self._cache[shield_file] = str(self.sounds_dir / shield_file)

        # 8. Dash / Blink whoosh
        dash_file = "dash.wav"
        if not (self.sounds_dir / dash_file).exists():
            duration = 0.20
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 280 + 1100 * math.sin(math.pi * t)
                amp = math.sin(math.pi * t) * 0.45
                s = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * s)
            self._write_wav(dash_file, samples)
        else:
            self._cache[dash_file] = str(self.sounds_dir / dash_file)

        # 9. EMP shockwave
        emp_file = "emp.wav"
        if not (self.sounds_dir / emp_file).exists():
            duration = 0.45
            total_samples = int(rate * duration)
            samples = []
            for i in range(total_samples):
                t = i / total_samples
                freq = 70 + 400 * (1.0 - t)
                amp = (1.0 - t) * 0.55
                s = math.sin(2 * math.pi * freq * (i / rate))
                # Add harsh ring mod
                ring = math.sin(2 * math.pi * 90 * (i / rate))
                samples.append(amp * s * ring)
            self._write_wav(emp_file, samples)
        else:
            self._cache[emp_file] = str(self.sounds_dir / emp_file)

        # 10. Coin / Scrap pickup
        scrap_file = "pickup.wav"
        if not (self.sounds_dir / scrap_file).exists():
            duration = 0.10
            total_samples = int(rate * duration)
            samples = []
            half = total_samples // 2
            for i in range(total_samples):
                freq = 880 if i < half else 1320
                t_env = 1.0 - (i / total_samples)
                amp = t_env * 0.35
                s = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * s)
            self._write_wav(scrap_file, samples)
        else:
            self._cache[scrap_file] = str(self.sounds_dir / scrap_file)

        # 11. Powerup fanfare
        powerup_file = "powerup.wav"
        if not (self.sounds_dir / powerup_file).exists():
            duration = 0.32
            total_samples = int(rate * duration)
            samples = []
            notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
            segment = total_samples // len(notes)
            for i in range(total_samples):
                idx = min(len(notes) - 1, i // segment)
                freq = notes[idx]
                t_sub = (i % segment) / segment
                amp = (1.0 - t_sub) * 0.38
                s = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * s)
            self._write_wav(powerup_file, samples)
        else:
            self._cache[powerup_file] = str(self.sounds_dir / powerup_file)

        # 12. Boss alarm klaxon
        boss_file = "boss_alarm.wav"
        if not (self.sounds_dir / boss_file).exists():
            duration = 0.40
            total_samples = int(rate * duration)
            samples = []
            half = total_samples // 2
            for i in range(total_samples):
                freq = 440 if (i // (rate // 10)) % 2 == 0 else 330
                t_env = 1.0 - (i / total_samples) * 0.5
                amp = t_env * 0.4
                s = math.sin(2 * math.pi * freq * (i / rate))
                samples.append(amp * s)
            self._write_wav(boss_file, samples)
        else:
            self._cache[boss_file] = str(self.sounds_dir / boss_file)

    def play(self, sound_name: str):
        """Play sound asynchronously without blocking gameplay."""
        if not self.enabled or not HAS_WINSOUND:
            return
        
        filename = f"{sound_name}.wav" if not sound_name.endswith(".wav") else sound_name
        filepath = self._cache.get(filename)
        if not filepath:
            filepath = str(self.sounds_dir / filename)
            if not os.path.exists(filepath):
                return
            self._cache[filename] = filepath

        try:
            # PlaySound with SND_ASYNC | SND_FILENAME executes in the Windows audio subsystem thread
            winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass


# Singleton instance
sound_engine = SoundEngine()
