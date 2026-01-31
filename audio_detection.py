import sounddevice as sd
import numpy as np
import requests
import time

device_id = 5


# --- Settings ---
FS = 44100              # Sample rate
THRESHOLD = 0.25        # Ignore quiet sounds
CHUNK_DURATION = 1      # Seconds per audio chunk

# Frequency bands (Hz)
SIREN_BAND = (700, 1300)
SPEECH_BAND = (100, 500)
FIRE_BAND = (3000, 4000)

# Persistence counters
siren_hits = 0
fire_hits = 0

# Backend APE endpoint 
BACKEND_URL = "http://localhost:8080/api/events"

# State tracking
current_state = "idle" # "idle", "siren", "fire"
last_detected_time = time.time()        # time when siren/fire was last detected
IDLE_BUFFER = 3                         # seconds to keep alarm displayed after sound dips


# Mapping Python state -> backend type
STATE_TO_TYPE = {
    "idle": "IDLE",
    "siren": "SIREN_ALARM",
    "fire": "FIRE_ALARM"
}

# --- Helper functions ---
def sanity_check_backend():
    """Check if backend is running before starting."""
    try:
        r = requests.get("http://localhost:8080/api/health", timeout=2)
        if r.status_code == 200:
            print("Backend is running")
            return True
    except Exception:
        pass
    print("Backend not reachable. Make sure it is running.")
    return False

def send_event(state):
    """Send state change event to backend."""
    payload = {"type": STATE_TO_TYPE[state], "ts": 0}
    try:
        requests.post(BACKEND_URL, json=payload)
        print(f"Sent event: {payload['type']}")
    except Exception as e:
        print("Failed to send event to backend:", e)

# --- Main Loop ---
if not sanity_check_backend():
    exit(1)

print("Listening... Press Ctrl+C to stop")

try:
    while True:
        # Record 1 second of audio
        audio = sd.rec(int(FS * CHUNK_DURATION), samplerate=FS, channels=1, device = device_id)
        sd.wait()
        audio = audio.flatten()

        max_amp = np.max(np.abs(audio))

        # Initialize for debug
        siren_energy = 0
        fire_energy = 0

        if max_amp < THRESHOLD:
            siren_hits = 0
            fire_hits = 0
            detected_state = "idle"
        else:
            # Compute FFT
            fft_data = np.abs(np.fft.rfft(audio))
            fft_freq = np.fft.rfftfreq(len(audio), d=1/FS)

            # --- Siren Detection ---
            siren_energy = np.sum(fft_data[(fft_freq > SIREN_BAND[0]) & (fft_freq < SIREN_BAND[1])])
            speech_energy = np.sum(fft_data[(fft_freq > SPEECH_BAND[0]) & (fft_freq < SPEECH_BAND[1])])

            if siren_energy > 2.0 * speech_energy: #tweak this factor if needed
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
            elif siren_hits >= 2:
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
            print(current_state)
            send_event(current_state)
        
        print(f"Max amp: {max_amp:.3f}, Siren energy: {siren_energy:.1f}, Fire energy: {fire_energy:.1f}, Detected: {detected_state}")
       
except KeyboardInterrupt:
    print("\nStopped by user")