# Project Lifecycle

## Core Tech Stack

| Component       | Technology               | Why?                                                         |
|-----------------|--------------------------|--------------------------------------------------------------|
| Language        | Python 3.11+             | Best libraries for NLP, voice processing, and OS automation. |
| Voice-to-Text   | OpenAI Whisper (Local)   | High accuracy, runs locally on your GPU/CPU (no API costs).  |
| NLP / Intent    | Ollama (Llama 3/Mistral) | Turns "Clean up my desktop" into `os.remove()` commands locally. |
| OS Interaction  | `os` and `shutil`        | Standard Python tools for file manipulation.                 |
| GUI (Frontend)  | CustomTkinter or Flet    | Modern, dark-mode UIs that look like native Windows apps.    |

---

## System Architecture: How It Flows

A smooth application should not just "run a script." It needs a pipeline that handles the full transition from sound to action.

**The Workflow:**

1. **Listener** — A background thread monitors for a wake word (e.g., "Hey Assistant").
2. **Transcriber** — Whisper converts the audio buffer into text.
3. **Interpreter (The Brain)** — An LLM parses the text to extract the Action (Delete), Target (File Name), and Path (Folder).
4. **Safety Logic** — A middleware check ensures system-critical files are never accidentally touched.
5. **Execution** — The file system performs the edit or deletion.

---

## Folder Structure

```
AI_Command_Project/
├── main.py           # The UI and entry point
├── processor.py      # Logic for Ollama and Whisper
├── file_manager.py   # Logic for deleting/editing files
└── requirements.txt  # List of libraries
```

---

## Learning Phases

### Phase 1 — The Foundation (Core Python)
**Priority:** High | **Estimated Time:** 1–2 Weeks

You cannot build an AI system without a solid grasp of the language running it.

**What to learn:** Variables, functions, dictionaries (very important for JSON), and `try/except` blocks (so your app doesn't crash when a file is missing).

**Where to learn:**
- **YouTube:** Programming with Mosh — *Python Tutorial for Beginners* (the first 2 hours are sufficient).
- **Articles:** Real Python — *Python Basics*.
- **Documentation:** Official Python Tutorial.

---

### Phase 2 — The "Hands" (File System Operations)
**Priority:** High | **Estimated Time:** 3–5 Days

You need to learn how to make Python interact with your files.

**What to learn:** The `os` module, the `shutil` module, and the `send2trash` library. Practice creating, renaming, and moving files using code.

**Where to learn:**
- **YouTube:** "Python File Management" by Tech with Tim or Corey Schafer.
- **Articles:** *Automate the Boring Stuff* — Chapter 9 (Organizing Files). This is the go-to reference for this kind of work.

---

### Phase 3 — The "Brain" (Ollama & Prompt Engineering)
**Priority:** Medium | **Estimated Time:** 3–5 Days

This is where you learn to turn a sentence like "Get rid of the old logs" into a structured command.

**What to learn:** How to install Ollama, how to write a system prompt that forces the AI to respond in JSON, and how to use the `requests` library in Python to communicate with Ollama.

**Where to learn:**
- **YouTube:** Matthew Berman's Ollama Guide — covers running models locally.
- **Documentation:** Ollama's GitHub API Docs.

---

### Phase 4 — The "Ear" (Faster Whisper)
**Priority:** Medium | **Estimated Time:** 3 Days

Converting your voice input into text.

**What to learn:** How to use the `faster-whisper` library and how to record audio using `pyaudio` or `sounddevice`.

**Where to learn:**
- **YouTube:** "Speech Recognition in Python" by NeuralNine.
- **Article:** Faster-Whisper GitHub README (the examples are beginner-friendly and easy to follow).

---

### Phase 5 — The "Face" (UI with Flet)
**Priority:** Low | **Estimated Time:** 1 Week

Making the application look like a real Windows app.

**What to learn:** Layouts (Rows, Columns), Buttons, and TextFields in Flet.

**Where to learn:**
- **Documentation:** Flet.dev — *Get Started* (well-written, with copy-paste-ready code examples).
- **YouTube:** The Line Code — great Flet tutorials for beginners.

---

## Beginner's Strategy for Success

Do not try to build everything at once. Build it in this exact order:

1. **Script 1** — A script that deletes a specific hardcoded file when you run it.
2. **Script 2** — A script where you *type* "delete" and it deletes the file.
3. **Script 3** — A script where you *say* "delete" and it deletes the file.
4. **Final** — Wrap everything in a UI window.