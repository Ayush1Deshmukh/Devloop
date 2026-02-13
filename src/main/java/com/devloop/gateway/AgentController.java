package com.devloop.gateway;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/agent")
public class AgentController {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String PYTHON_SERVICE_URL = "http://devloop-api:8000/api/v1/generate";

    @PostMapping("/execute")
    public ResponseEntity<Object> processRequest(@RequestBody Map<String, Object> body) {
        try {
            Object response = restTemplate.postForObject(PYTHON_SERVICE_URL, body, Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Error connecting to AI Engine: " + e.getMessage());
        }
    }
}
