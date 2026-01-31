import sounddevice as sd
import numpy as np

#Settings
fs = 44100 #sample rate
threshold = 0.2 #tweak if needed

print("Press Ctrl+C to stop")

try:
    while True:
        audio = sd.rec(int(fs *1), samplerate=fs, channels=1)
        sd.wait()
        max_amp = np.max(np.abs(audio))
        if max_amp > threshold:
            print("ALERT: Loud sound detected!")
except KeyboardInterrupt:
    print("\nStopped by user")