import sounddevice as sd
import numpy as np
import requests
import time

#Settings
fs = 44100 # sample rate
threshold = 0.35 # amplitude threshold to ignore quiet sounds
chunk_duration = 1 #seconds per audio chunk

# Frequency bands (Hz)
SIREN_BAND = (800, 1200)
SPEECH_BAND = (100, 500)
FIRE_BAND = (3000, 4000)

# Persistence counters
siren_hits = 0
fire_hits = 0

# Backend APE endpoint (replace with actual endpoint)
BACKEND_URL = "http://localhost:8080/event"

# Cooldown (seconds)
COOLDOWN_SECONDS = 5
last_event_time = 0

print("Listening... Press Ctrl+C to stop")

try:
    while True:
        # Record 1 second of audio
        audio = sd.rec(int(fs * chunk_duration), samplerate=fs, channels=1)
        sd.wait()
        audio = audio.flatten() # convert from 2D array to 1D

        max_amp = np.max(np.abs(audio))

        # skip quiet sounds
        if max_amp < threshold:
            siren_hits = 0
            fire_hits = 0
            continue # skip quiet chunks

        # Compute FFT
        fft_data = np.abs(np.fft.rfft(audio))
        fft_freq = np.fft.rfftfreq(len(audio), d=1/fs)

        # --- Siren Detection ---
        # Check if most energy is in high-frequency range (e.g., 500-2000Hz)
        siren_energy = np.sum(fft_data[(fft_freq > SIREN_BAND[0]) & (fft_freq < SIREN_BAND[1])])
        speech_energy = np.sum(fft_data[(fft_freq > SPEECH_BAND[0]) & (fft_freq < SPEECH_BAND[1])])

        if siren_energy > 3 * speech_energy: #tweak this factor if needed
            siren_hits += 1
        else:
            siren_hits = 0

        if siren_hits >= 4 and current_time - last_event_time > COOLDOWN_SECONDS:
            print("SIREN DETECTED")
            # Send event to backend
            try:
                requests.post(BACKEND_URL, json={"event": "siren"})
                last_event_time = current_time
            except Exception as e:
                print("Failed to send to backend: ", e)
            siren_hits = 0
        
        # --- Fire Alarm Detection ---
        fire_energy = np.sum(fft_data[(fft_freq > FIRE_BAND[0]) & (fft_freq < FIRE_BAND[1])])
        total_energy = np.sum(fft_data)

        if fire_energy > 0.3 * total_energy: 
            fire_hits += 1
        else:
            fire_hits = 0

        if fire_hits >= 2 and current_time - last_event_time > COOLDOWN_SECONDS:
            print("FIRE ALARM DETECTED")
            # Send event to backend
            try:
                requests.post(BACKEND_URL, json={"event": "fire"})
                last_event_time = current_time
            except Exception as e:
                print("Failed to send to backend: ", e)
            fire_hits = 0


except KeyboardInterrupt:
    print("\nStopped by user")