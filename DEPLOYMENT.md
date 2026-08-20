# 🚀 Deploying DevLoop for Free

Every component below runs on a permanently free tier. No credit card is required
at any step.

---

## Topology

| Component | Host | Free? | Notes |
|---|---|---|---|
| Neural Console (Streamlit) | Streamlit Community Cloud | ✅ Free forever | Sleeps when idle, wakes on visit |
| AI Engine (FastAPI) | Hugging Face Spaces **or** Render | ✅ Free | Spaces sleeps after ~48h idle; Render after ~15 min |
| Gateway (Spring Boot) | Render | ✅ Free | ~50s cold start after sleeping |
| Cache / rate limits (Redis) | Upstash | ✅ Free | 10k commands/day |
| Sandbox | ⚠️ **Not deployable** | — | See "The sandbox caveat" below |

---

## ⚠️ The sandbox caveat — read this first

Locally, `docker-compose` runs generated code inside a dedicated container. **That
cannot be reproduced on any free host**, because it requires mounting
`/var/run/docker.sock`, which every free platform blocks (it is a container-escape
vector).

So on a deployed instance, `tools.py` automatically switches to an **rlimit
sandbox** instead. It is not a container, but it is real isolation:

| Protection | Mechanism | Deployed (Linux) |
|---|---|---|
| Runaway loops | wall-clock timeout + `RLIMIT_CPU` | ✅ Enforced |
| Memory bombs | `RLIMIT_AS` / `RLIMIT_DATA` | ✅ Enforced |
| Fork bombs | `RLIMIT_NPROC` | ✅ Enforced |
| Disk filling | `RLIMIT_FSIZE` | ✅ Enforced |
| **API key theft** | environment rebuilt from an allowlist | ✅ Enforced |
| File-system blast radius | throwaway temp directory per run | ✅ Enforced |
| Kernel-level isolation | namespaces / cgroups | ❌ Docker only |

> On macOS, `RLIMIT_AS` is accepted but silently ignored by the kernel, so the
> memory cap is a no-op *locally on a Mac*. The timeout still contains anything
> runaway, and every deploy target is Linux, where it is enforced.

Be honest about this in your README: the Docker sandbox is the local/production
design; the deployed demo uses OS-level limits.

---

## 1. Get a Gemini API key

**Both keys this project has used are dead, and the reason matters.**

An early key was committed in plaintext to `debug_ai.py` and is still present in
~18 commits of git history. Google scans public repos and suspends leaked keys —
and the suspension lands on the **Cloud project**, not just the one key. The
current key in `.env` (a different key, in that same project) is therefore also
dead, returning `403 CONSUMER_SUSPENDED` for `projects/868682975015`.

So the fix is *not* "make another key":

1. Create a **brand-new Google Cloud project** — a key minted inside the
   suspended project inherits the suspension.
2. Create the API key in that new project: <https://aistudio.google.com/app/apikey>
3. Put it only in host secret managers and your local `.env` (gitignored).
4. Verify it before deploying: launch the UI and press **🩺 Test this key**, or
   run `python check_models.py`.

### Guards now in place against a repeat

| Guard | What it stops |
|---|---|
| `.gitignore` → `.env` | The key reaching a commit |
| `.dockerignore` → `.env` | The key being baked into a published image layer |
| `logic.py` redacts `AIza…` | The key echoing into on-screen logs from Google error bodies |
| `debug_ai.py` reads from env | The original hardcoding pattern that caused this |

The historic key remains in git history. It is already dead so there is nothing
to exploit, but if you want a clean history before making the repo public, purge
it with `git filter-repo --path debug_ai.py --invert-paths` (or BFG) and
force-push. That rewrites SHAs — coordinate with anyone who has a clone.

---

## 2. Neural Console → Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to <https://share.streamlit.io> → **New app**.
3. Repository: your repo · Branch: `main` · Main file: **`app.py`**
4. Open **Advanced settings → Secrets** and paste (TOML format):

```toml
GOOGLE_API_KEY = "AIza...your_new_key"
FREE_RUNS_PER_SESSION = "3"
LLM_MODEL = "gemini-2.0-flash"
LLM_BACKUP_MODEL = "gemini-2.5-flash"
DEVLOOP_MAX_ITERATIONS = "3"
```

5. Deploy.

`.streamlit/config.toml` is committed and applies the dark theme automatically.
See `.streamlit/secrets.toml.example` for every supported key.

### How the quota protection works

Each visitor gets `FREE_RUNS_PER_SESSION` runs on **your** key. After that the
run button disables and they are prompted to paste **their own** free Gemini key,
which grants unlimited runs on their quota.

Their key is held in `st.session_state` only — never written to `os.environ`,
never logged, never persisted. This matters: Streamlit Cloud serves every visitor
from one Python process, so a global would leak one visitor's key to strangers.
The agent is rebuilt per run via `create_agent(key)` so the key lives only in
that graph's closures.

Set `FREE_RUNS_PER_SESSION = "0"` to require every visitor to bring their own key
— then your quota can never be touched at all.

---

## 3. Redis → Upstash

1. Sign up at <https://upstash.com> (free, no card).
2. Create a Redis database, region close to your API host.
3. Copy the **`rediss://`** URL (TLS — `redis-py` negotiates it from the scheme).
4. Use it as `REDIS_URL` in step 4/5.

Optional. Without it, the rate limiter falls back to an in-memory counter that
works fine for a single instance.

---

## 4. AI Engine → Hugging Face Spaces

Spaces only builds a `Dockerfile` at the **repo root** — which is exactly what the
root `Dockerfile` is (port 7860, non-root UID 1000).

1. <https://huggingface.co/new-space> → SDK: **Docker** → Blank.
2. Push this repo to the Space remote.
3. **Settings → Variables and secrets**:
   - Secret `GOOGLE_API_KEY` = your key
   - Variable `LLM_MODEL` = `gemini-2.0-flash`
   - Variable `LLM_BACKUP_MODEL` = `gemini-2.5-flash`
   - Variable `DEVLOOP_MAX_ITERATIONS` = `3`
   - Variable `RATE_LIMIT_PER_MINUTE` = `10`
   - Secret `REDIS_URL` = your Upstash URL (optional)
   - Variable `BACKEND_CORS_ORIGINS` = `https://<your-app>.streamlit.app`
4. Verify: `https://<user>-<space>.hf.space/health`

`BACKEND_CORS_ORIGINS` accepts a plain comma-separated list or a JSON array.

---

## 5. Gateway + Engine → Render (one blueprint)

`render.yaml` defines both services on the free plan.

1. <https://dashboard.render.com> → **New → Blueprint** → select this repo.
2. Render reads `render.yaml` and creates `devloop-gateway` and `devloop-api`.
3. Fill the two secrets marked `sync: false`:
   - `GOOGLE_API_KEY`
   - `REDIS_URL` (optional)
4. `DEVLOOP_ENGINE_URL` is wired to the engine service automatically.

Verify:

```bash
curl https://devloop-gateway.onrender.com/api/v1/agent/health
```

```bash
curl -X POST https://devloop-gateway.onrender.com/api/v1/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"objective":"Write a function that reverses a string"}'
```

> The gateway URL was previously hardcoded to `http://devloop-api:8000`, which
> only resolves inside docker-compose. It now reads `DEVLOOP_ENGINE_URL`, so the
> same jar works locally and deployed.

---

## Keeping it genuinely free

**The hosting is free. Your Gemini quota is the scarce resource.** Free-tier
Gemini is capped per minute and per day; the free hosts have no such limit.

Layers already protecting you, outermost first:

1. **Per-visitor run quota** (`FREE_RUNS_PER_SESSION`) — Streamlit UI.
2. **Per-IP rate limit** (`RATE_LIMIT_PER_MINUTE`, default 20) — FastAPI middleware.
3. **Agent iteration cap** (`DEVLOOP_MAX_ITERATIONS`) — each iteration is one LLM
   call, so 3 is much cheaper than 5.
4. **Backup model fallback** — a 429 on `gemini-2.0-flash` retries on
   `gemini-2.5-flash` rather than failing.

If your quota still gets drained, set `FREE_RUNS_PER_SESSION = "0"` and let every
visitor bring their own key. The demo then works forever, for free, no matter how
much traffic it gets.

### Cold starts

| Host | Sleeps after | Wake time |
|---|---|---|
| Streamlit Cloud | ~7 days idle | a few seconds |
| Hugging Face Spaces | ~48 hours idle | ~30s |
| Render (free) | ~15 minutes idle | ~50s |

Nothing breaks — the first request after a nap is just slow. If you demo this
live, load the page a minute beforehand.

---

## ✅ Pre-deploy checklist

Run these locally before pushing. All of them are also enforced by CI
(`.github/workflows/python-package-conda.yml`).

```bash
flake8 .                     # 0 issues
pytest -q                    # 6 passed
bandit -r app -ll            # 0 medium/high
mvn -B clean package         # gateway compiles + 4 tests pass
docker compose config -q     # 5 services resolve
docker compose build         # every Dockerfile builds from a clean checkout
python check_models.py       # your key works and lists usable models
```

Then confirm, by hand:

- [ ] `GOOGLE_API_KEY` is set in each **host's** secret manager, not in any file you committed.
- [ ] `git log -S 'AIza' --all` returns nothing you care about (see step 1 if it does).
- [ ] `LLM_MODEL` is a model `check_models.py` actually listed for your key.
- [ ] `BACKEND_CORS_ORIGINS` on the engine names your real Streamlit URL.
- [ ] `FREE_RUNS_PER_SESSION` is set to what you can afford on your quota (`"0"` = visitors must bring their own key).

---

## Local development (full Docker sandbox)

The deployed setup is the degraded one. For the real architecture:

```bash
cp .env.example .env   # add your GOOGLE_API_KEY
docker compose up --build -d
```

- Neural Console → <http://localhost:8501>
- Gateway → <http://localhost:8080/api/v1/agent/execute>
- Engine docs → <http://localhost:8000/docs>

With the sandbox container running, `tools.py` uses real Docker isolation
automatically — it probes with `docker inspect` and only falls back to rlimits
when the container is genuinely unavailable.
