# SeniorLiving AI — Intelligent Voice Sales & Appointment Booking Agent

## Overview

SeniorLiving AI is an AI-powered voice agent designed to handle incoming enquiries for a senior living community.

It conducts natural, consultative conversations, understands prospective residents' needs, answers questions using verified community information, captures contact details, and helps qualified prospects schedule appointments.

This is an independent AI engineering portfolio project.

## Core Capabilities

- Natural, real-time English voice conversations
- Context-aware discovery and qualification
- Grounded answers from a verified community knowledge base
- Contact information extraction and confirmation
- Conversation summaries and structured lead records
- Appointment availability checks and booking
- CRM contact creation and updates
- Repeat-caller recognition
- Graceful handling of interruptions, uncertainty, and booking failures

## Technology Stack

| Component | Technology |
| Backend | Python, FastAPI |
| Voice orchestration | LiveKit Agents |
| Speech recognition | faster-whisper |
| Language model | Ollama with a local model |
| Speech generation | Piper TTS |
| Data storage | SQLite initially; PostgreSQL planned |
| Scheduling | Calendly |
| CRM destination | Google Sheets |
| Testing | pytest |
| Version control | Git and GitHub |

## Architecture

The system is designed around modular components:

- Agent: conversation orchestration and decision-making
- Voice: speech recognition, synthesis, and real-time audio
- Conversation: dialogue state and lead qualification
- Knowledge: verified community information and retrieval
- Scheduling: appointment availability and booking
- CRM: contact records and conversation summaries
- Evaluation: automated quality and reliability testing
- API: application endpoints and integration layer

## Development Principles

- Prioritise free and local technologies where practical.
- Never fabricate community information or appointment confirmations.
- Confirm contact details before saving them.
- Avoid duplicate contacts when an existing lead is recognised.
- Keep external integrations modular and testable.
- Measure performance through repeatable evaluations.
- Protect personal information and use authorised sample data.

## Project Scope — Version 1

One demo senior living community, one English-language voice agent, one appointment event type, and one CRM destination.

Outbound calling, multiple communities, additional languages, and full sales-call archive processing are excluded from Version 1.

## Development Status

Currently in initial environment and repository setup.

## Disclaimer

This is a portfolio demonstration, not a production healthcare or emergency-response service. The agent does not provide medical advice.

## GPU Inference Optimization & Performance Benchmark

### Hardware Configuration

| Component | Specification |
| Laptop | Dell Latitude 5420 |
| CPU | Intel Core i7-1185G7 |
| CPU cores / threads | 4 / 8 |
| RAM | 31.39 GB |
| GPU | Intel Iris Xe Graphics |
| GPU backend | Vulkan |
| Inference engine | Ollama / llama.cpp |
| LLM | Llama 3.2 3B |
| Ollama version | 0.40.15 |

### GPU Acceleration

Configured Ollama to use the Intel Iris Xe integrated GPU through its Vulkan backend.

GPU detection and inference were verified using `ollama ps`, which reported:

- Processor allocation: 100% GPU
- Model: `llama3.2:3b`
- Context window: 4096 tokens

### Inference Performance

Full system prompt benchmark:

| Metric | CPU inference | GPU inference |
|---|---:|---:|
| Prompt tokens | 1,755 | 1,755 |
| Generated tokens | 50 | 76 |
| Prompt processing | 139.31 s | 8.55 s |
| Response generation | 7.33 s | 4.78 s |
| Total inference | 146.90 s | 13.38 s |

**Prompt processing improvement: approximately 93.9%.**

Note: Prompt processing times are comparable because both runs processed the same 1,755-token prompt. Total inference times are indicative only because the runs generated different numbers of response tokens.

### Validation

- Ollama integration test: 1 passed.
- Regression suite: 124 passed, 1 deselected.
- Full system instructions retained during GPU benchmark.
- No regression failures observed.

### Engineering Significance

This optimization demonstrates hardware-aware local LLM deployment, Vulkan-based GPU acceleration, inference profiling, and regression validation.

The benchmark was conducted on a local development machine. Performance may vary across hardware, drivers, model versions, and workloads.