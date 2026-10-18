# EchoLight - Real-Time Sound Detection & Visual Alerts

EchoLight is an accessibility-focused web application developed during ElleHacks 2026 to help deaf and hard-of-hearing users become more aware of important sounds in their environment.

The application analyzes audio for patterns associated with emergency sirens and fire alarms, then communicates detected events to a web interface that displays visual notifications.

**[View our project on Devpost](https://devpost.com/software/echolight)**

## Features
- **Real-time audio analysis**: Captures audio in one-second intervals and uses Fast Fourier Transform (FFT) to analyze frequency patterns.
- **Emergency sound detection**: Identifies potential emergency sirens and fire alarms using frequency-band comparisons.
- **Visual notifications**: Displays screen flashes, animated icons, and alert banners when a sound is detected.
- **Live event streaming**: Uses Server-Sent Events (SSE) to communicate detection events from the backend to the web interface.
- **Connection management**: The frontend automatically attempts to reconnect if its connection to the backend is interrupted.
- **Detection stability**: Uses consecutive detections and a short persistence buffer to reduce brief or inconsistent alerts.

## Technologies
| Component | Technologies |
| --- | ---|
| Audio detection | Python, NumPy, sounddevice |
| Backend | Java 17, Spring Boot 4.0.2, Maven |
| Frontend | HTML, CSS, JavaScript |
| Communication | HTTP REST API, Server-Sent Events (SSE) |

## How It Works
EchoLight consists of three components that communicate through a locally hosted backend.
### 1. Python audio detector
   The `audio_detection.py` script captures audio at 44,100 Hz and processes it in one-second chunks.
   It uses NumPy's FFT implementation to examine frequency-band energy and detect patterns associated with emergency sirens and fire alarms.
   To reduce false positives, a sound must meet its detection criteria across multiple consecutive audio chunks before triggering an alert.
   
### 2. Spring Boot backend
   The backend acts as a communication layer between the audio detector and the web interface.
   - `POST /api/events` - Receives detection events from Python.
   - `GET /api/stream` - Streams events to connected clients using SSE.
   - `GET /api/health` - Provides a basic backend health check.
   The backend also stores the most recent event and sends it to newly connected clients.

### 3. Web frontend
   The frontend is built using HTML, CSS, and JavaScript. When the user clicks **Start**, JavaScript establishes an SSE connection to the backend.
   It responds to incoming events by displaying visual alerts for detected sounds. The interface also provides connection status information and a Stop button to disconnect from the event stream.

## Running Locally
#### Prerequisites
- Java 17 or newer
- Python 3
- A compatible audio input device
- A modern web browser

### 1. Clone the repository
```
git clone https://github.com/KristinaBBBB/ElleHacks-EchoLight.git
cd ElleHacks-EchoLight
```

### 2. Start the backend
   Navigate to the backend directory:
   ```bash
   cd backend
   ```
   
   On Windows: 
   ```powershell
   .\mvnw.cmd spring-boot:run
   ```

   On macOS/Linux: 
   ```bash
   ./mvnw spring-boot:run
   ```
   
   The backend runs at [http://localhost:8080](http://localhost:8080) by default.
   You can verify that it is running by visiting: [http://localhost:8080/api/health](http://localhost:8080/api/health)
   
### 3. Start audio detection
   Open another terminal in the repository's root directory.
   Install the Python dependencies: `pip install numpy sounddevice requests`

   Before running the script, check the `device_id` variable in `audio_detection.py`. It is currently set to 7, which was the audio device index used during development and may need to be changed for another computer.

   Start detection: 
   ```bash
   python audio_detection.py
   ```
   
   The script checks that the backend is reachable before beginning audio analysis.
   
### 4. Open the frontend
   Open `main.html` in your browser, using a local development server if needed.

   Click **Start** to connect to the backend's event stream.

   **Note**: The Start button controls the frontend connection. It does not launch the Python detector, which must be started separately.

## Limitations
EchoLight was developed as a hackathon proof of concept rather than a production-ready application.
- Detection uses frequency-based heuristics rather than a trained classification model, so false positives and missed detections are possible.
- The audio detector currently requires manual startup and configuration of the input device.
- The application was designed for local execution and has not been prepared for production deployment.
- The prototype is not a substitute for certified emergency detection or alert systems.

## Team & Development
EchoLight was developed collaboratively during ElleHacks 2026.

The project combines Python audio processing, a Java Spring Boot backend, and a browser-based interface. The components were developed and integrated during the hackathon to demonstrate real-time sound-to-visual notifications.

See the [Devpost submission](https://devpost.com/software/echolight) for the project presentation and team information.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
