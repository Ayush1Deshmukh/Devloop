package com.devloop.gateway;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/agent")
public class AgentController {

    // The engine URL was hardcoded to the docker-compose service name, which
    // only resolves inside that network. Injected from configuration so the same
    // jar works locally and on a free host where the engine is a public URL.
    private final String pythonServiceUrl;

    private final RestTemplate restTemplate;

    public AgentController(
            RestTemplateBuilder builder,
            @Value("${devloop.engine.url:http://devloop-api:8000}") String engineBaseUrl,
            @Value("${devloop.engine.timeout-seconds:120}") long timeoutSeconds) {
        this.pythonServiceUrl = normalizeBaseUrl(engineBaseUrl) + "/api/v1/generate";
        // Free-tier engines cold-start slowly, so allow a generous read timeout —
        // but never an unbounded one, which would pin a gateway thread forever.
        this.restTemplate = builder
                .setConnectTimeout(Duration.ofSeconds(15))
                .setReadTimeout(Duration.ofSeconds(timeoutSeconds))
                .build();
    }

    /**
     * Ensures the engine base URL carries a scheme.
     *
     * <p>Render's blueprint supplies this via {@code fromService property: hostport},
     * which yields a bare {@code host:port} with no scheme. RestTemplate rejects
     * that ("URI is not absolute"), so every deployed gateway request failed with
     * a 502 before it left the process.
     *
     * <p>A host with no dot is a container/service name (docker-compose's
     * {@code devloop-api}), which is plain HTTP on an internal network. Anything
     * with a dot is a real hostname and gets HTTPS.
     */
    static String normalizeBaseUrl(String raw) {
        String url = raw == null ? "" : raw.trim().replaceAll("/+$", "");
        if (url.isEmpty()) {
            return "http://devloop-api:8000";
        }
        if (url.matches("(?i)^https?://.*")) {
            return url;
        }
        String host = url.split("/", 2)[0].split(":", 2)[0];
        boolean internal = host.equals("localhost")
                || host.equals("127.0.0.1")
                || !host.contains(".");
        return (internal ? "http://" : "https://") + url;
    }

    @PostMapping("/execute")
    public ResponseEntity<Object> processRequest(@RequestBody Map<String, Object> body) {
        try {
            Object response = restTemplate.postForObject(pythonServiceUrl, body, Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            // 502: the gateway is fine, the upstream engine is not.
            return ResponseEntity.status(502).body(Map.of(
                    "error", "Could not reach the AI Engine",
                    "detail", String.valueOf(e.getMessage()),
                    "engine", pythonServiceUrl
            ));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Object> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "engine", pythonServiceUrl
        ));
    }
}
