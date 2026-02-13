# 🔧 DevLoop Troubleshooting Guide

### 🔴 Issue: "Docker Socket Permission Denied"
**Symptom:** API logs show `permission denied` when trying to run docker commands.
**Fix:** `sudo chmod 666 /var/run/docker.sock`

### 🔴 Issue: "Redis Connection Refused"
**Symptom:** Health check shows `redis_connected: false`.
**Fix:**
1. Check if Redis is running: `docker ps`
2. Restart: `docker-compose up -d --force-recreate redis`

### 🔴 Issue: "LLM Rate Limit Exceeded"
**Symptom:** 429 Error from Google API.
**Fix:**
Wait 60 seconds. The API has a `RATE_LIMIT` fallback in `app/middleware/rate_limiter.py` but Google's hard limit might be hit during heavy testing.

### 🔴 Issue: "Tests not found"
**Symptom:** Pytest says `file not found`.
**Fix:**
Ensure the volume mount in `docker-compose.yml` is correct (`.:/workspace` for sandbox). The API writes files to disk, and the Sandbox reads them from the shared volume