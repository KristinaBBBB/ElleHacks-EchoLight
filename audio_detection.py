import sounddevice as sd
import numpy as np

#Settings
fs = 44100 # sample rate
threshold = 0.2 # amplitude threshold to ignore quiet sounds
chunk_duration = 1 #seconds per audio chunk

print("Press Ctrl+C to stop")

try:
    while True:
        # Record 1 second of audio
        audio = sd.rec(int(fs * chunk_duration), samplerate=fs, channels=1)
        sd.wait()
        audio = audio.flatten() # convert from 2D array to 1D

        max_amp = np.max(np.abs(audio))
        if max_amp > threshold:
            continue # skip quiet chunks

        # Compute FFT
        fft_data = np.fft.rfft(audio)
        fft_freq = np.fft.rfftfreq(len(audio), d=1/fs)

        # Simple siren detection:
        # Check if most energy is in high-frequency range (e.g., 500-2000Hz)
        high_freq_energy = np.sum(np.abs(fft_data[(fft_freq > 500) & (fft_freq < 2000)]))
        low_freq_energy = np.sum(np.abs(fft_data[(fft_freq > 100) & (fft_freq <= 500)]))

        if high_freq_energy > 1.5 * low_freq_energy: #tweak this factor if needed
            print("SIREN DETECTED")
        else:
            print("Loud sound, but not a siren")

except KeyboardInterrupt:
    print("\nStopped by user")