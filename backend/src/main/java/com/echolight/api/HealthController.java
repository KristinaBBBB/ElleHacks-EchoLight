package com.echolight.api;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/")
    public String home() {
        return "EchoLight backend running";
    }

    @GetMapping("/api/health")
    public String health() {
        return "ok";
    }
}
