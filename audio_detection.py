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

# Backend APE endpoint 
BACKEND_URL = "http://localhost:8080/event"

# State tracking
current_state = "idle" # possible values: "idle", siren", "fire"

# Idle buffer (seconds)
IDLE_BUFFER = 3
last_detected_time = time.time() # time when siren/fire was last detected

# Mapping Python state -> backend type
STATE_TO_TYPE = {
    "idle": "IDLE",
    "siren": "SIREN_ALARM",
    "fire": "FIRE_ALARM"
}

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
            detected_state = "idle"
        else:
            # Compute FFT
            fft_data = np.abs(np.fft.rfft(audio))
            fft_freq = np.fft.rfftfreq(len(audio), d=1/fs)

            # --- Siren Detection ---
            # Check if most energy is in high-frequency range (e.g., 500-2000Hz)
            siren_energy = np.sum(fft_data[(fft_freq > SIREN_BAND[0]) & (fft_freq < SIREN_BAND[1])])
            speech_energy = np.sum(fft_data[(fft_freq > SPEECH_BAND[0]) & (fft_freq < SPEECH_BAND[1])])

            if siren_energy > 2.5 * speech_energy: #tweak this factor if needed
                siren_hits += 1
            else:
                siren_hits = 0
        
            # --- Fire Alarm Detection ---
            fire_energy = np.sum(fft_data[(fft_freq > FIRE_BAND[0]) & (fft_freq < FIRE_BAND[1])])
            total_energy = np.sum(fft_data)

            if fire_energy > 0.25 * total_energy: 
                fire_hits += 1
            else:
                fire_hits = 0

            # Decide current detected state
            if fire_hits >= 2:
                detected_state = "fire"
            elif siren_hits >= 3:
                detected_state = "siren"
            else:
                detected_state = "idle"

            # Update Last detected time if an alarm is active
            if detected_state in ["fire", "siren"]:
                last_detected_time = time.time()
        
        # --- Apply idle buffer ---
        if detected_state == "idle":
            if time.time() - last_detected_time < IDLE_BUFFER:
                #still within buffer, keep previous state
                detected_state = current_state
        
        # --- Send event if state changed ---
        if detected_state != current_state:
            current_state = detected_state
            backend_payload = {
                "type": STATE_TO_TYPE[current_state],
                "ts": 0
            }
            try:
                requests.post(BACKEND_URL, json=backend_payload)
                print(f"Sent event: {backend_payload['type']}")
            except Exception as e:
                print("Failed to send event to backend: ", e)


except KeyboardInterrupt:
    print("\nStopped by user")