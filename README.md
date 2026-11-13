# SeniorLiving AI — Intelligent Voice Sales & Appointment Booking Agent

An AI-powered voice-agent prototype for senior living enquiries, prospective resident discovery, and lead qualification.

> **Project status:** Functional portfolio prototype. English voice conversations have been tested end to end. Some external integrations and multilingual capabilities remain experimental or planned.

---

## 1. Overview

SeniorLiving AI is an AI engineering project that explores how conversational AI and real-time voice technology can improve the way senior living communities handle prospective resident enquiries.

The system is designed to engage callers in natural conversations, understand their needs, answer questions using verified community information, collect relevant lead details, and preserve conversation context.

The demonstration uses **WillowBrook Senior Living**, a fictional senior living community created for this project.

The objective is to demonstrate a modular, locally deployable AI voice-agent architecture that combines speech recognition, language models, speech synthesis, conversation management, knowledge grounding, and persistent data storage.

This is an independent AI engineering portfolio project.

## 2. Problem Statement

Senior living communities receive enquiries from prospective residents and family members who often need information about accommodation, services, facilities, and the process of arranging a visit.

Traditional enquiry handling can involve:

- Repetitive questions from prospective residents and families.
- Delays in responding to enquiries.
- Inconsistent information across conversations.
- Manual collection of prospective resident information.
- Difficulty maintaining context across multiple interactions.

SeniorLiving AI explores an AI-powered approach to these challenges through a conversational voice interface.

The agent is intended to provide an accessible first point of contact while leaving sensitive, complex, or unconfirmed matters to the community's human team.

## 3. Core Capabilities

### Implemented capabilities

- **Real-time voice interaction:** LiveKit-based voice-agent orchestration.
- **Speech recognition:** Faster-Whisper transcription of caller audio.
- **Local language model inference:** Llama 3.2 3B through Ollama.
- **Speech generation:** Piper text-to-speech.
- **Conversation management:** Context-aware conversation state and multi-turn dialogue.
- **Knowledge grounding:** Responses based on available community information.
- **Lead discovery:** Extraction of relevant information from caller conversations.
- **Conversation persistence:** SQLite-based storage.
- **Language metadata:** Detection of caller language and language-aware response prompting.
- **Fallback handling:** Graceful handling of selected language-model failures.
- **Automated testing:** Unit and integration-oriented regression tests using pytest.

### Capabilities requiring further integration or validation

The following are not presented as completed production capabilities:

- Live Calendly availability checks and confirmed appointment booking.
- Production Google Sheets or external CRM synchronisation.
- Verified repeat-caller identification across production deployments.
- Complete multilingual voice conversations in Yoruba, Igbo, and Hausa.
- Production-grade monitoring, deployment, and operational security.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| Real-time voice orchestration | LiveKit Agents |
| Speech recognition | Faster-Whisper |
| Language model | Llama 3.2 3B |
| Local inference runtime | Ollama |
| Text-to-speech | Piper TTS |
| Database | SQLite |
| Testing | pytest |
| Version control | Git and GitHub |

### Why a local AI stack?

The project prioritises locally runnable and cost-conscious AI components where practical.

Using Ollama allows the language model to run locally rather than requiring every inference request to be sent to a hosted LLM API.

This approach is useful for experimentation, cost control, and understanding the engineering requirements of self-hosted AI systems.

Local deployment does not automatically guarantee privacy or production security; those require additional controls.

## 5. System Architecture

The application is organised into modular components.

| Component | Responsibility |
|---|---|
| `src/agent/` | Conversation orchestration, LLM integration, and agent behaviour |
| `src/api/` | FastAPI application and API endpoints |
| `src/conversation/` | Conversation state and related dialogue functionality |
| `src/voice/` | Speech recognition, speech synthesis, and voice adapters |
| `src/knowledge/` | Community knowledge and grounded information |
| `src/scheduling/` | Scheduling-related functionality |
| `src/crm/` | Lead and CRM-related functionality |
| `src/evaluation/` | Evaluation and quality-testing functionality |

### Conversation flow

1. A caller joins a LiveKit voice session.
2. The voice agent receives the caller's audio.
3. Faster-Whisper converts speech into text and provides detected-language metadata.
4. The conversation engine processes the caller's message and available conversation context.
5. The language model generates a response, subject to the system's instructions and grounding approach.
6. Piper generates spoken audio.
7. The voice agent returns the response to the caller.
8. Conversation information can be persisted through the application's storage layer.

## 6. Multilingual Development

The project has begun implementing language-aware conversation handling.

The initial language targets are:

- English
- Yoruba
- Igbo
- Hausa

The speech-recognition pipeline has been extended to preserve detected-language metadata. The conversation layer can also pass supported language information into its response instructions.

**Important limitation:** This does not establish complete multilingual support.

The verified end-to-end spoken experience is English. Yoruba, Igbo, and Hausa recognition and response prompting remain experimental and require testing with representative native-speaker audio.

The current Piper voice configuration is English-language. Multilingual speech synthesis has not been verified.

Future multilingual development will require suitable speech models, quality evaluation, and licensing checks for commercial use.

## 7. Installation and Setup

### Prerequisites

- Python 3.12
- Git
- [Ollama](https://ollama.com/)
- [LiveKit Cloud](https://cloud.livekit.io/) account and project credentials
- LiveKit CLI
- A local copy of this repository

### Clone the repository

```powershell
git clone https://github.com/A-D-T-Workspace/senior-living-ai-voice-agent.git

cd senior-living-ai-voice-agent
```

### Create and activate a virtual environment

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

### Install core dependencies

```powershell
pip install -r requirements.txt
```

### Install voice and LiveKit dependencies

The voice-processing packages are installed separately from `requirements.txt`.

```powershell
pip install livekit==1.1.21 livekit-agents==1.8.10 livekit-api==1.2.2 livekit-plugins-silero==1.8.10 faster-whisper==1.2.1 piper-tts==1.8.0
```

### Configure Ollama

Install and start Ollama, then download the configured model:

```powershell
ollama pull llama3.2:3b
```

Confirm that the model is available:

```powershell
ollama list
```

### Configure the Piper voice model

The project uses the Piper English voice model:

```text
models/piper/en_US-lessac-medium.onnx
```

The corresponding configuration is:

```env
PIPER_VOICE=models/piper/en_US-lessac-medium.onnx
```

Both the `.onnx` model and its `.onnx.json` configuration file are included in the project.

### Configure environment variables

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure the following settings:

**Application and security**
- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `SECRET_KEY`

**Local LLM**
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

**Voice processing**
- `WHISPER_MODEL`
- `PIPER_VOICE`

**Database**
- `DATABASE_URL`

**LiveKit**
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

**Optional integrations**
- `CALENDLY_ACCESS_TOKEN`
- `CALENDLY_EVENT_TYPE_URI`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`

Calendly and Google Sheets settings are configuration placeholders; their live integrations have not yet been validated.

Never commit `.env` files, API keys, access tokens, or other secrets to Git. Replace the development secret with a securely generated value before any deployment.

## 8. Running the Application

The API and voice worker run in separate terminals.

### Terminal 1 — Start the API

```powershell
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — Start the LiveKit worker

```powershell
python -m src.agent.worker dev
```

The worker should connect to the configured LiveKit environment.

### Create a voice session

With the API running, create a session:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/sessions" -Method POST -ContentType "application/json" -Body "{}"
```

Use the returned session information according to the application's response.

The LiveKit room can be joined using the corresponding room identifier and the configured LiveKit CLI workflow.

Actual voice operation depends on the API, worker, local model runtime, credentials, and audio environment being correctly configured.

## 9. Testing and Evaluation

Testing is an important part of the project's development.

The project uses pytest to validate individual components and their interactions.

Run the test suite:

```powershell
pytest tests -q
```

### Latest verified regression result

<escape>156 passed</escape>

This result reflects the full test run recorded on **13 November 2026**.

The tests cover areas including:

- Conversation engine behaviour.
- Language-aware response instructions.
- LiveKit LLM integration.
- Speech recognition and language metadata.
- Voice adapters.
- Response grounding.
- Conversation handling and fallback behaviour.

Passing automated tests demonstrate that the tested software behaviours work under the test conditions. They do not independently establish production reliability, multilingual speech quality, or commercial readiness.

## 10. Engineering Considerations

### Grounded responses

The agent is designed to use available community information rather than inventing services, prices, facilities, or care capabilities.

When the required information is unavailable, the agent should acknowledge the limitation and direct the caller to the community team.

### Reliability

The conversation engine includes fallback handling for selected LLM failures. Further work is required to evaluate reliability under extended conversations, service interruptions, and high concurrent usage.

### Performance

The current local inference environment uses Llama 3.2 3B through Ollama.

Inference latency depends on the hardware, model configuration, prompt length, and runtime. No verified GPU acceleration claim is made in this project documentation.

### Privacy

The application handles potentially sensitive information about prospective residents and their families.

A production deployment would require appropriate consent, data minimisation, access controls, retention policies, encryption, secure infrastructure, and applicable legal and regulatory review.

## 11. Current Limitations

The following limitations define the boundary between the portfolio prototype and a production service:

1. **English-first voice experience:** Complete multilingual spoken conversations have not been validated.
2. **Speech synthesis:** The configured Piper voice is English-language.
3. **Scheduling:** Confirmed live appointment availability and booking are not established.
4. **CRM:** Production external CRM synchronisation is not established.
5. **Scalability:** Production load testing and concurrent-call capacity have not been established.
6. **Monitoring:** Production observability, alerting, and operational monitoring require further work.
7. **Commercial licensing:** All model, voice, dataset, and dependency licences must be reviewed before commercial deployment.

## 12. Roadmap

| Priority | Planned improvement |
|---|---|
| High | Improve speech-recognition accuracy in real-world conversations |
| High | Evaluate conversation quality, factual accuracy, and response latency |
| High | Complete licensing and privacy review |
| High | Implement and validate appointment scheduling |
| Medium | Integrate an external CRM |
| Medium | Improve repeat-caller recognition and lead lifecycle management |
| Medium | Evaluate Yoruba, Igbo, and Hausa speech recognition |
| Medium | Integrate commercially suitable multilingual speech synthesis |
| Future | Production deployment, monitoring, and scalability testing |

## 13. Project Significance

SeniorLiving AI demonstrates practical AI engineering across several interconnected areas:

- Real-time voice-agent architecture.
- Local LLM deployment and integration.
- Speech-to-text and text-to-speech pipelines.
- Context-aware conversational systems.
- Knowledge-grounded generation.
- Structured lead discovery.
- Persistent conversation storage.
- Multilingual pipeline experimentation.
- Automated software testing and reliability engineering.

The project is designed to show how individual AI components can be combined into a working conversational application rather than simply demonstrating an isolated language-model prompt.

## 14. Disclaimer

WillowBrook Senior Living is a fictional demonstration community created for this portfolio project. It is not a real senior living facility.

SeniorLiving AI is a software engineering prototype. It is not a healthcare provider, does not provide medical advice, and is not an emergency-response service.

The prototype must not be relied upon to make clinical, medical, or care-placement decisions.

---

## Repository

**GitHub:** https://github.com/A-D-T-Workspace/senior-living-ai-voice-agent

**Project:** SeniorLiving AI — Intelligent Voice Sales & Appointment Booking Agent

**Status:** Functional AI voice-agent portfolio prototype