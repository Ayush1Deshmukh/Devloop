# ⚡ DevLoop: Autonomous DevSecOps Architect (Enterprise Edition)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://devloop-4btrpio39tggj8yvpnyt2q.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Java 17](https://img.shields.io/badge/Java-17-red.svg)](https://www.oracle.com/java/technologies/downloads/)
[![Powered by LangGraph](https://img.shields.io/badge/Powered%20by-LangGraph-orange)](https://langchain-ai.github.io/langgraph/)

> **The "Self-Healing" Microservices Code Engine.**  
> DevLoop is an agentic AI system that autonomously writes, tests, secures, and fixes software. Now upgraded to a **Polyglot Microservices Architecture** for enterprise-scale reliability.

---

## 🎥 System Demonstration

<div align="center">
  <img src="demoo.gif" alt="DevLoop Autonomous Coding Demo" width="100%">
  <p><em>Watch the agent autonomously write code, detect failures, and self-correct in real-time.</em></p>
</div>

<br>

<div align="center">
  
**[🔴 LIVE DEMO → Access the Neural Console](https://devloop-4btrpio39tggj8yvpnyt2q.streamlit.app/)**

</div>

---

## 🚀 The Evolution: Why Microservices?

Modern AI systems require **Separation of Concerns**. DevLoop has evolved from a single script into a distributed system:

| 🏗️ Service | Technology | Responsibility |
|:---:|:---:|:---|
| **API Gateway** | **Spring Boot** | Enterprise ingress, request routing, and security |
| **AI Engine** | **FastAPI** | LangGraph orchestration and LLM state management |
| **Memory** | **Redis** | Persistence of agent states and rate-limiting |
| **Sandbox** | **Docker** | Isolated, secure execution of generated artifacts |

---

## 📸 Screenshots

<div align="center">

### 🖥️ Command Center Dashboard
<img src="Screenshot 1.png" alt="DevLoop Dashboard" width="90%">
<p><i>Cyberpunk-themed interface with real-time terminal logs and glassmorphism UI</i></p>

<br>

### 🛡️ Security Audit Report
<img src="screenshot 2.png" alt="Security Audit" width="90%">
<p><i>Automated vulnerability detection using Bandit static analysis</i></p>

</div>

---

## 🏗️ System Architecture

```mermaid
graph TD
    User[👤 User] -->|POST 8080| GW[🛡️ Spring Boot Gateway]
    GW -->|REST Call| API[🧠 FastAPI AI Engine]
    API -->|Manage State| Redis[(💾 Redis Cache)]
    API -->|Iterative Build| Agent[👨‍💻 LangGraph Agent]
    Agent -->|Execute Code| Box[🐳 Docker Sandbox]
    
    Box -->|Feedback| Agent
    Agent -->|Result| API
    API -->|Final Response| GW
    GW -->|Success| User

    subgraph "Docker Network"
    GW
    API
    Redis
    Box
    end
```

---

## 🔄 The Autonomous Self-Healing Loop

| Step | Agent | Action |
|------|-------|--------|
| 1️⃣ | Architect | Analyzes objective → Writes failing pytest unit tests (TDD) |
| 2️⃣ | Developer | Writes implementation code to pass those tests |
| 3️⃣ | SecOps | Scans code with Bandit for vulnerabilities (SQLi, Shell injection, etc.) |
| 4️⃣ | Tester | Executes code in sandboxed environment |
| 🔁 | Self-Correction | If tests fail OR vulnerabilities found → Loop back to Developer |

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Orchestration | LangGraph — Cyclic State Management |
| Backend (Gateway) | Java 17, Spring Boot 3.x |
| Backend (AI) | Python 3.11, FastAPI |
| LLM | Google Gemini 1.5 Flash |
| Infrastructure | Docker, Docker Compose, Redis |
| Frontend | Streamlit + Custom Glassmorphism UI |

---

## 📂 Project Structure

```plaintext
DevLoop/
├── src/main/java/       # 🛡️ Gateway — Spring Boot Java Source
├── app/                 # 🧠 AI Engine — Python FastAPI Source
│   ├── core/agents/     # LangGraph node definitions
│   ├── api/routes/      # Endpoint logic
│   └── main.py          # FastAPI Entry Point
├── docker/              # 📦 Infrastructure — Dockerfiles for Java/Python/Sandbox
├── docker-compose.yml   # 🕸️ Orchestrator — Multi-container networking
├── pom.xml              # 📋 Maven Dependencies
├── requirements.txt     # 📋 Python Dependencies
├── .env.example         # 🔑 Secret Configuration Template
└── README.md            # 📖 Documentation
```

---

## ⚡ Quick Start (Enterprise Deployment)

### Prerequisites

- Docker & Docker Compose  
- Google Gemini API Key  

---

### 1️⃣ Configure Secrets

Create a `.env` file in the root directory:

```bash
GOOGLE_API_KEY="your_api_key_here"
```

---

### 2️⃣ Build and Launch

Deploy the entire 4-container stack with a single command:

```bash
# Build the Java artifact using a builder container
docker run --rm -v "$(pwd)":/app -w /app maven:3.9.6-eclipse-temurin-17 mvn clean package -DskipTests

# Launch the Microservices
docker-compose up --build -d
```

---

### 3️⃣ Access the System

- Gateway API: http://localhost:8080/api/v1/agent/execute  
- Neural Console (UI): http://localhost:8501  

---

## 🌟 Key Features

- 🏗️ **Polyglot Architecture** — Java stability for ingress, Python flexibility for AI.  
- 🔄 **Autonomous TDD** — Tests written before implementation.  
- 🛡️ **Security-First** — Every iteration scanned for vulnerabilities using Bandit.  
- 🔁 **Self-Healing** — Reads stack traces, fixes its own bugs in real-time.  
- 🐳 **Sandboxed Execution** — High-security code execution in isolated containers.  

---

## 👨‍💻 Author

<div align="center">

**Ayush Deshmukh**  
Third-Year Computer Science & Engineering  

</div>

---

<div align="center">

🚀 Built for the Future of Agentic Software Engineering  

⭐ Star this repo if you find it useful!

</div>
