# singularity_codex

# Zuno AI – Your Personal Linux Desktop Assistant

Zuno AI is a smart, voice- and text-controlled assistant built for Linux.  
Think of it as your always-on digital buddy who can help you manage files, browse the web, control media, check the weather, and even chat with you — all from simple natural language commands.

It connects with **Large Language Models (LLMs)** via OpenRouter, talks to your system utilities, and hooks into everyday apps and APIs to get things done.

---

## ✨ What Zuno AI Can Do

Here’s a taste of what Zuno can handle:

- 🎤 **Voice or Text Commands** – Speak naturally or just type your request.
- 📂 **File & Folder Management** – Create, delete, move, and rename files or whole directories.
- 🌍 **Online Search** – Quickly look things up or open websites for you.
- 📊 **System Info & Stats** – Keep tabs on CPU, RAM, battery, and network usage.
- 🎶 **Music Control** – Play songs on YouTube, pause, skip, or go back to previous tracks.
- 🌦 **Weather** – Get real-time weather updates for any city.
- 📄 **Document Handling** – Read and summarise PDFs, Word files, and even images via OCR.
- 💬 **Messaging** – Send WhatsApp messages or Gmail emails right from your desktop.
- 🖼 **Wallpaper Management** – Change wallpapers instantly or set up auto-rotation.
- 🔊 **System Controls** – Adjust brightness, audio, Wi-Fi, and more.
- 🗑 **Trash Management** – Safely move unwanted files or folders to the trash.

---

## 🛠 Under the Hood

Zuno AI is powered by **Python 3** and integrates with an exciting mix of technologies:

- **Selenium** – For browser automation & WhatsApp control
- **PyMuPDF**, **python-docx**, **pytesseract** – For document reading and OCR
- **psutil** – For system monitoring
- **gTTS** & **playsound** – Text-to-Speech
- **LangChain** + **OpenRouter APIs** – LLM integration
- Linux utilities & DBus commands for wallpaper, PDF extraction, and more

---

![Image](https://github.com/user-attachments/assets/bf0af5d6-413f-4482-ae87-f6a2c1e4a6d7)

![Image](https://github.com/user-attachments/assets/fa6da40e-3b16-488b-af14-daa35f1ba716)

## 📂 Project Layout

- `backend.py` – The brain: all logic and actions live here  
- `ui.py` – The face: optional interface plus a vision/screenshot module  
- `llm_agent.py` – Handles talking to the LLM and parsing its responses  

---
