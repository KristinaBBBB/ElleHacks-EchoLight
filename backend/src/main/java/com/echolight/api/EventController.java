package com.echolight.api;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
@RequestMapping("/api")
public class EventController {

    private final List<SseEmitter> clients = new CopyOnWriteArrayList<>();
    private volatile DetectionEvent lastEvent = new DetectionEvent("HOME", System.currentTimeMillis());

    @PostMapping("/events")
    public void receiveEvent(@RequestBody DetectionEvent incoming) {
        lastEvent = new DetectionEvent(incoming.type(), System.currentTimeMillis());
        broadcast(lastEvent);
    }
    @PostMapping("/transcript")
    public void receiveTranscript(@RequestBody TranscriptRequest req) {

         String translated = req.text(); // MVP: echo for now

        Map<String, Object> payload = new HashMap<>();
        payload.put("kind", "TRANSLATION");
        payload.put("source", "speech");
        payload.put("from", req.from());
        payload.put("to", req.to());
        payload.put("original", req.text());
        payload.put("translated", translated);
        payload.put("ts", System.currentTimeMillis());

        for (SseEmitter emitter : clients) {
             try {
                 emitter.send(payload);
        } catch (IOException e) {
            clients.remove(emitter);
        }
    }
}

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(0L);
        clients.add(emitter);

        emitter.onCompletion(() -> clients.remove(emitter));
        emitter.onTimeout(() -> clients.remove(emitter));
        emitter.onError(e -> clients.remove(emitter));

        try { emitter.send(lastEvent); } catch (IOException ignored) {}
        return emitter;
    }

    private void broadcast(DetectionEvent ev) {
        for (SseEmitter emitter : clients) {
            try { emitter.send(ev); }
            catch (IOException e) { clients.remove(emitter); }
        }
    }
}
