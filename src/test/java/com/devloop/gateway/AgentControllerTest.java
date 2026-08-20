package com.devloop.gateway;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AgentControllerTest {

    @Test
    void keepsAnExplicitScheme() {
        assertEquals("http://devloop-api:8000",
                AgentController.normalizeBaseUrl("http://devloop-api:8000"));
        assertEquals("https://engine.example.com",
                AgentController.normalizeBaseUrl("https://engine.example.com"));
    }

    @Test
    void addsHttpsToASchemelessPublicHost() {
        // This is exactly what Render's `fromService property: hostport` produces.
        assertEquals("https://devloop-api.onrender.com:443",
                AgentController.normalizeBaseUrl("devloop-api.onrender.com:443"));
    }

    @Test
    void addsHttpToAContainerServiceName() {
        assertEquals("http://devloop-api:8000",
                AgentController.normalizeBaseUrl("devloop-api:8000"));
        assertEquals("http://localhost:8000",
                AgentController.normalizeBaseUrl("localhost:8000"));
    }

    @Test
    void stripsTrailingSlashesAndBlankInput() {
        assertEquals("http://devloop-api:8000",
                AgentController.normalizeBaseUrl("http://devloop-api:8000///"));
        assertEquals("http://devloop-api:8000", AgentController.normalizeBaseUrl("   "));
        assertEquals("http://devloop-api:8000", AgentController.normalizeBaseUrl(null));
    }
}
