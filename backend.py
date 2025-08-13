import os
from selenium.common.exceptions import TimeoutException
import fitz
import re
import subprocess
import sys
import difflib
import mimetypes
import docx
from PIL import Image
import pytesseract
import shutil
import webbrowser
import requests
import json
import platform
import glob          
import send2trash 
#int
import threading
import time
import base64
import pickle
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psutil
import shlex # command parsing klie
from llm_agent import get_llm_response
from gtts import gTTS
import playsound
import tempfile
import os


PROFILE_PATH = "/home/anas/.config/BraveSoftware/Brave-Browser/Default"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
BRAVE_BINARY = "/usr/bin/brave"
# --- Browser Session State ---
browser_session = {
    "driver": None,
    "current_url": None,
    "last_search": None,
    "last_query": None,
}

from llm_agent import get_llm_response
from gtts import gTTS
import playsound
import tempfile
import os

def speak_response(text: str):
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        tts.save(temp_path)
        playsound.playsound(temp_path)
        os.remove(temp_path)
    except Exception as e:
        print(f"❌ TTS Error: {e}")
    return "\n".join(results)

def extract_llm_intent(user_message):
    memory_file = "memory.txt"
    memory_data = ""
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                memory_data = f.read().strip()
        except Exception as e:
            print(f"⚠️ Could not load memory: {e}")
    system_prompt = """
You are an intelligent Linux desktop voice/text agent. 
DATA = MEMORY.TXT:
{memory_data}
Always remember this data. Maintain continuity over sessions and may use it if the user asks something we discussed earlier.
Recognize user intent and output *only* JSON in this schema (no extra explanation):
Do NOT include <think> or any explanation. Output must be only a valid JSON object or array of them.
{"action":"...", ...}
Either a single JSON object:
{"action":"...", ...}

Or an array of multiple actions:
[
  {"action":"...", ...},
  {"action":"...", ...}
]
You are allowed to return a list of multiple actions as a JSON array.

Example:
User says: "In Music folder, create palindrome.c and write a program"
→ Respond with:
[
  {"action":"create_folder", "folder_path":"~/Music"},
  {"action":"create_file", "folder_path":"~/Music", "filename":"palindrome.c", "content":"..."}
]

If folder already exists, the create_folder action is still valid — it won't overwrite anything.

- Always resolve folder paths as if they are inside the user's home directory.
- Example: "in downloads" → "~/Downloads"
- Example: "in downloads/code/level1" → "~/Downloads/code/level1"
- Example: "in music/notes/old" → "~/Music/notes/old"
- Never use '/home/user' or '/path/to/...'
- Always return folder paths using tilde (~) syntax: ~/Downloads/... or ~/Music/...
- Do NOT assume ~/Documents unless user says "Documents"

If user says "my name is X" or "remember my name is X",
→ {"action": "remember_name", "name": "X"}

If user asks "what is my name" or "tell me my name",
→ {"action": "get_name"}


Supported actions:
- chat: for info, answer, chitchat, or if no other action matches
- create_folder: {"action":"create_folder", "folder_path":"/absolute/or/~/relative/path"}
- create_project: {"action":"create_project", "project_name":"Calculator", "location":"~/Documents", "language":"cpp", "gui":true/false}
- create_file: {"action":"create_file", "folder_path":"~/path", "filename":".extension", "content":"..." If the user says:
- control_volume: {"action": "control_volume","amount"}
- "Create a file named [filename] and write [text/poem/notes/code/about X] in it", 
then
- Extract the '[filename]' as the filename, 
- For the 'content' field, do NOT just copy '[text/poem/notes/code/about X]' verbatim.
- Instead, generate meaningful content relevant to the description. 
  For example, if the user says 'about Bengalis', generate a short informative paragraph about Bengali people, their culture, festivals, food, etc.
- Use paraphrasing and content generation capabilities of the model to provide rich informative content, not just replicate user input.
If the user says:
- "Create a file named [filename] and write [text/poem/notes/code/about X] in it",
  - Extract '[filename]' as the filename.
  - For the 'content' field: DO NOT copy user's words verbatim. Instead,
      * If asked for a code/program ("C code for palindrome", "Python code for sorting list", etc.), generate a complete, working solution. For instance, write a full function or main program, including input/output, suitable comments, and tested logic.
      * If asked for a poem, info, or descriptive topic (e.g. "about Bengalis"), generate several paragraphs or stanzas truly explaining, describing, or performing the requested content.
  - Use the model’s creativity and paraphrasing skills to provide rich, relevant content.
  - If user only says "create file named [filename]", do not include 'content' (create empty file).
  
- file_exists: {"action":"file_exists", "filename":"...", "type":"file" or "folder" or "any"}

- open_file: {"action":"open_file", "filename":"..."}
- play_music: {"action":"play_music", "song":"Song Name"}
- stop_music: {"action":"stop_music"}
- wifi_status: {"action":"wifi_status"}
- next_music: {"action":"next_music"}
- fix_code: {"action":"fix_code", "file_path":"~/path/to/code.ext"}

- get_weather: {"action":"get_weather", "city":"Nagpur"}
- move_file_folder: {"action":"move_file_folder", "source_path":"~/path/to/file_or_folder", "destination_path":"~/path/to/destination_folder"}

- wifi_status: {"action":"wifi_status"}
- bluetooth_devices: {"action":"bluetooth_devices"}
- connected_devices: {"action":"connected_devices"}
- general_knowledge: {"action":"general_knowledge", "question":"Who is the CEO of Tesla?"}
- process_document: {"action":"process_document", "file_path":"~/Documents/file.pdf", "query":"Summarize" }
  # Works for PDF, DOCX, and image files (JPEG/PNG). If 'query' is omitted, returns summary. If given, answers the question.
- list_dir_contents: {"action":"list_dir_contents", "path":" ", "type":"files" or "folders" or "all"}

- trash_files: {"action":"trash_files", "path_pattern":"<path>"} # Moves files/folders to the system trash. Can handle single files, directories, and wildcards (*).
  - Always use real file paths like '~/Music/filename.ext'.
  If user says:
  - "delete file X in folder Y"
  - "remove main.c from inside palindrome program"
  - "delete a file from Documents/subfolder"
→ Respond with:
{"action":"delete_file", "filepath":"~/Documents/subfolder/main.c"}

If a subfolder is mentioned (like 'inside palidrone program'), resolve the full path and use delete_file.

Never default to create_file or create_folder unless verbs like "create", "make", or "generate" are used.
  - Example (file): User says "trash the screenshot.png file from Downloads" -> {"action":"trash_files", "path_pattern":"~/Downloads/screenshot.png"}
  - Example (folder): User says "delete the 'java utility' folder from documents" -> {"action":"trash_files", "path_pattern":"~/Documents/java utility"}
This will trash the entire contents of the folder.

Do NOT use delete_file for folders.

  - Example: User says "trash the screenshot.png file from Downloads" -> {"action":"trash_files", "path_pattern":"~/Downloads/screenshot.png"}
- change_wallpaper: {"action":"change_wallpaper", "image_path":"/path/to/image.jpg"}
- system_usage: {"action":"system_usage"}
- network_info: {"action":"network_info"}
- system_usage: {"action":"system_usage"}

- network_info: {"action":"network_info"}
- delete_file:  If user says "delete a folder" or "delete a directory", or uses folder-related words,
→ Use: {"action":"trash_files", "path_pattern":"~/Documents/foldername/*"}
    This will trash the entire contents of the folder.
    Do NOT use delete_file for folders.
  {"action":"delete_file", "filepath":"/path/to/file.txt"}
- change_wallpaper: {"action":"change_wallpaper", "image_path":"/path/to/image.jpg"}
- previous_music: {"action":"previous_music"}
- open_browser: {"action":"open_browser"}
- navigate_to: {"action":"navigate_to", "url":"..."}
- search_website: {"action":"search_website", "query":"..."}
- save_note: {"action": "save_note", "filename": "xyz.txt", "content": "your content"}
- remind_me: {"action": "remind_me", "message": "your message", "after_minutes": 10}
- search_web: {"action": "search_web", "query": "Who won India vs England latest test series"}
- send_whatsapp: {"action":"send_whatsapp", "contact":"...", "message":"..."}
- tell_time: {"action":"tell_time"}
- rename_file: {"action":"rename_file", "filepath":"~/Downloads/pytorch.pdf", "newname":"pytorchai.pdf"}
- tell_date: {"action":"tell_date"}
- announce: {"action":"announce", "message":"..."}
- network_info: {"action":"network_info"} # For fetching IPv4 and IPv6 addresses
If user says in Hindi/English like:
"xyz@gmail.com ko mail bhejo ki kal mai college nahi aarha hu"
or "Send email to rahul@example.com saying meeting postponed"

Then:
→ {"action":"send_email", "recipient":"<email>", "message":"<full message text>"}

Subject is optional — will be generated from message later.

- system_info: {"action":"system_info"}
- battery_status: {"action":"battery_status"}
- change_brightness: {"action":"change_brightness", "amount": -50}
- extract_pdf_text: {"action":"extract_pdf_text", "query":"..."}
If the request does not match these, default to {"action":"chat", "message":"..."} with a concise answer.
Never output any explanation outside of JSON!
"""
    prompt = system_prompt + "\n\nUser message: " + user_message
    llm_out = get_llm_response(prompt, code_only=False).strip()
    llm_out = re.sub(r'<think>.*?</think>', '', llm_out, flags=re.DOTALL).strip()
    llm_out = get_llm_response(prompt, code_only=False).strip()
    match = re.search(r'(\[.*?\]|\{.*?\})', llm_out, re.DOTALL)

    if match:
        try:
            parsed = json.loads(match.group(1))
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception as e:
            print("❌ JSON parse error:", e)

    # fallback if no valid JSON matched
    return [{"action": "chat", "message": llm_out}]

def resolve_folder_path(user_path):
    # Convert 'Documents/testing' -> '~/Documents/testing'
    user_path = user_path.strip().replace("/home/user", "~")
    # Ensure it doesn't become "//testing"
    if user_path.startswith("/"):
        user_path = "~" + user_path
    if not user_path.startswith("~"):
        user_path = os.path.join("~", user_path)
    full_path = os.path.expanduser(user_path)
    return full_path

def do_create_folder(folder_path, folder_name=None):
    try:
        folder_path = os.path.expanduser(folder_path)
        if folder_name:
            folder_path = os.path.join(folder_path, folder_name)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return f"✅ Folder created at: {folder_path}"
    except Exception as e:
        return f"❌ Could not create folder: {e}"


def fuzzy_find_path(user_input, search_dirs_only=False, search_files_only=False):
    user_input = os.path.basename(user_input.strip().lower())
    home_dir = str(Path.home())
    all_matches = []

    for root, dirs, files in os.walk(home_dir):
        items = dirs if search_dirs_only else files if search_files_only else dirs + files
        for name in items:
            score = difflib.SequenceMatcher(None, user_input, name.lower()).ratio()
            if score >= 0.7:
                full_path = os.path.join(root, name)
                all_matches.append((score, full_path))

    if not all_matches:
        return None

    all_matches.sort(reverse=True, key=lambda x: x[0])
    return all_matches[0][1]

import subprocess


def do_control_volume(amount: int):
    """
    Adjusts system volume.
    Positive → increase, Negative → decrease.
    """
    try:
        if not amount:
            return "❌ Please specify a volume change amount."

        change = f"{abs(amount)}%"
        if amount > 0:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{change}"], check=True)
        else:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{change}"], check=True)

        direction = "increased" if amount > 0 else "decreased"
        return f"🔊 Volume {direction} by {abs(amount)}%."

    except FileNotFoundError:
        return "❌ 'pactl' command not found. This works only on Linux with PulseAudio/PipeWire."
    except Exception as e:
        return f"❌ Failed to change volume: {e}"


def do_list_dir_contents(path, type="all"):
    try:
        folder_path = os.path.expanduser(path)

        if not os.path.exists(folder_path):
            return f"❌ Path not found: {folder_path}"
        if not os.path.isdir(folder_path):
            return f"❌ Not a directory: {folder_path}"

        items = os.listdir(folder_path)
        files = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
        folders = [f for f in items if os.path.isdir(os.path.join(folder_path, f))]

        if type == "files":
            return f"📄 Files in {folder_path}: {', '.join(files) if files else 'None'}"
        elif type == "folders":
            return f"📁 Folders in {folder_path}: {', '.join(folders) if folders else 'None'}"
        elif type == "files_count":
            return f"📄 There are {len(files)} files in {folder_path}."
        elif type == "folders_count":
            return f"📁 There are {len(folders)} folders in {folder_path}."
        else:  # type == "all"
            return (
                f"Contents of {folder_path}:\n"
                f"📄 Files ({len(files)}): {', '.join(files) if files else 'None'}\n"
                f"📁 Folders ({len(folders)}): {', '.join(folders) if folders else 'None'}"
            )

    except Exception as e:
        return f"❌ Error while listing contents: {e}"
import os

def normalize_path(path_str: str):
    """Cleans, expands, and converts shorthand names to actual paths."""
    path_str = (path_str or "").strip()

    # If no path given, default to home directory
    if not path_str:
        return os.path.expanduser("~")

    # Handle shorthand user inputs
    lower_path = path_str.lower()
    if lower_path in ("desktop", "desk"):
        return os.path.expanduser("~/Desktop")
    if lower_path in ("documents", "docs"):
        return os.path.expanduser("~/Documents")
    if lower_path in ("downloads", "download"):
        return os.path.expanduser("~/Downloads")

    # Always expand ~ to home
    return os.path.expanduser(path_str)



def do_search_web(query):
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0"}
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        response = requests.post(url, headers=headers, data=data, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Get the first result block
        results = soup.select("a.result__a")
        if results:
            title = results[0].text.strip()
            return f"🌐 {title}"

        # Try fallback paragraph extraction
        snippets = soup.select("div.result__snippet")
        if snippets:
            return f"🌐 {snippets[0].text.strip()}"

        return f"❌ No meaningful answer found for: {query}"

    except Exception as e:
        return f"❌ Web search failed: {e}"


        return f"🌐 {snippet}" if snippet else "❌ No answer found."
    except Exception as e:
        return f"❌ DuckDuckGo search failed: {e}"

SESSION_CONTEXT_FILE = "session_context.json"

def load_context():
    if os.path.exists(SESSION_CONTEXT_FILE):
        try:
            with open(SESSION_CONTEXT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_context(ctx):
    with open(SESSION_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2)

def update_context_from_action(action_dict):
    """Store useful params from last executed action."""
    ctx = load_context()
    for k, v in action_dict.items():
        if k != "action" and isinstance(v, str) and v.strip():
            ctx[k.lower()] = v.strip()
    save_context(ctx)

def resolve_references_in_message(user_message):
    """Replace vague terms in message with last known context values."""
    ctx = load_context()
    msg = user_message
    for k, v in ctx.items():
        # Example replacements: "us folder" → last known folder path
        patterns = [f"us {k}", f"that {k}", f"wahi {k}", f"wo {k}"]
        for p in patterns:
            if p in msg.lower():
                msg = re.sub(re.escape(p), v, msg, flags=re.IGNORECASE)
    return msg

def do_get_weather(city_name=None):
    try:
        if not city_name:
            return "❌ Please specify a city to get weather info."

        url = f"https://wttr.in/{city_name}?format=3"
        resp = requests.get(url).text.strip()

        if "Unknown location" in resp:
            return f"❌ Weather info not available for '{city_name}'."

        return f"🌦️ {resp}"
    except Exception as e:
        return f"❌ Error fetching weather: {e}"
import psutil # Make sure this is at the top of your file

def do_trash_files(path_pattern):
    """
    Finds files/directories matching a pattern and moves them to the system Trash.
    Fuzzy matches files/folders even if the case or spelling is slightly off.
    """
    try:
        expanded_path = os.path.expanduser(path_pattern)
        items_to_trash = glob.glob(expanded_path)

        # If no exact glob match, try literal path or fuzzy
        if not items_to_trash:
            if os.path.exists(expanded_path):
                items_to_trash = [expanded_path]
            else:
                fuzzy_path = fuzzy_find_path(path_pattern)
                if fuzzy_path and os.path.exists(fuzzy_path):
                    items_to_trash = [fuzzy_path]
                else:
                    return f"🤷 No files or directories found matching: {path_pattern}"

        for item in items_to_trash:
            print(f"🚮 Moving to trash: {item}")
            send2trash.send2trash(item)

        count = len(items_to_trash)
        preview = ", ".join(os.path.basename(p) for p in items_to_trash[:3])
        if count > 3:
            preview += "..."
        item_type = "item" if count == 1 else "items"

        return f"✅ Moved {count} {item_type} to the Trash (e.g., {preview})."

    except Exception as e:
        return f"❌ Error while trying to move files to Trash: {e}"

def do_fix_code(file_path):
    """
    Intelligent version of code fixer.
    - Locates code file (supports fuzzy match)
    - Reads code and sends to LLM for repair
    - Handles syntax & logic errors
    - Tolerates LLM returning extra text, Markdown, or incomplete JSON
    - Cleans code before saving
    """
    import re, json, json5, os

    try:
        expanded_path = os.path.expanduser(file_path)

        # Locate file with fuzzy match
        resolved_path = fuzzy_find_path(expanded_path, search_files_only=True)
        if not resolved_path or not os.path.isfile(resolved_path):
            return f"❌ File not found: {file_path}"

        # Read current code
        with open(resolved_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        # Prompt for LLM repair (✅ Added original_code to prompt)
        fix_prompt = f"""
You are a highly skilled programming assistant.
Analyze the given code, detect errors, and fix them.

PHASE 1: Identify the main problem(s) in the code.
PHASE 2: If there is a SYNTAX error, fix only those lines to make the code executable.
PHASE 3: If there is a LOGIC error, fix the logic but preserve variable and function names where possible.

Respond with ONLY a valid JSON object in the following format:
{{
  "error_type": "syntax" or "logic",
  "error_location": "<brief human-readable location of the issue>",
  "fixed_code": "<full corrected code without markdown or backticks>"
}}

Here is the code to fix:

{original_code}
"""

        llm_out = get_llm_response(fix_prompt, code_only=False).strip()

        # Extract JSON object even if LLM adds extra text
        match = re.search(r'\{[\s\S]*\}', llm_out)
        if not match:
            return f"❌ Could not parse AI output.\nRaw output:\n{llm_out}"

        try:
            data = json5.loads(match.group())  # json5 tolerates single quotes, trailing commas
        except Exception as e:
            return f"❌ JSON parse error: {e}\nRaw output:\n{llm_out}"

        fixed_code = data.get("fixed_code", "").strip()
        if not fixed_code:
            return f"❌ AI did not return fixed code.\nRaw data:\n{data}"

        # Remove Markdown code fences if present
        if fixed_code.startswith("```"):
            fixed_code = re.sub(r"^```[a-zA-Z0-9]*\n?", "", fixed_code)
            fixed_code = re.sub(r"```$", "", fixed_code).strip()

        # Sanity check — ensure output is not too short
        if len(fixed_code) < len(original_code) * 0.5:
            return "⚠️ Warning: AI output may be incomplete. Code not replaced."

        # Save fixed code back to file
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        return (
            f"✅ Code fixed successfully!\n"
            f"🔹 Error Type: {data.get('error_type','unknown')}\n"
            f"📍 Location: {data.get('error_location','unknown')}\n"
            f"📂 File: {resolved_path}"
        )

    except Exception as e:
        return f"❌ Error fixing code: {e}"



def do_save_note(filename, content):
    try:
        notes_dir = os.path.expanduser("~/LuciferNotes")
        Path(notes_dir).mkdir(parents=True, exist_ok=True)

        filepath = os.path.join(notes_dir, filename if filename.endswith(".txt") else filename + ".txt")
        with open(filepath, "w") as f:
            f.write(content)

        subprocess.Popen(['kwrite', filepath])
        return f"📝 Note saved to: {filepath} (opened in KWrite)"
    except Exception as e:
        return f"❌ Could not save note: {e}"


def do_remind_me(message, after_minutes):
    def notify():
        time.sleep(after_minutes * 60)
        subprocess.run(['notify-send', 'Lucifer Reminder', message])
        subprocess.run(['espeak', f'Reminder: {message}'])

    threading.Thread(target=notify, daemon=True).start()
    return f"⏰ Reminder set for {after_minutes} minutes from now."


def do_get_network_info():
    """Fetches IPv4 and IPv6 addresses for all network interfaces."""
    addrs = psutil.net_if_addrs()
    info = "🌐 Network Information:\n"
    has_info = False
    for interface, addresses in addrs.items():
        # Skip the loopback interface
        if interface == 'lo':
            continue
            
        ipv4 = next((addr.address for addr in addresses if addr.family == psutil.AF_INET), "N/A")
        ipv6 = next((addr.address for addr in addresses if addr.family == psutil.AF_INET6), "N/A")
        
        # Only include interfaces that have a valid IP address
        if ipv4 != "N/A" or ipv6 != "N/A":
            info += f"- {interface}:\n  - IPv4: {ipv4}\n  - IPv6: {ipv6}\n"
            has_info = True

    if not has_info:
        return "❌ No active network interfaces with IP addresses were found."
        
    return info


def do_create_project(project_name, location, language, gui):
    try:
        # Fix LLM hallucination of /home/user
        location = location.replace("/home/user", "~")

        # Full project path
        base = os.path.expanduser(os.path.join(location, project_name))
        Path(base).mkdir(parents=True, exist_ok=True)

        skeleton_code = ""
        ext = ""
        language_lower = language.lower()
        gui = gui if isinstance(gui, bool) else False  # Fallback

        if language_lower in ["cpp", "c++"]:
            ext = "cpp"
            skeleton_code = '''#include <iostream>
using namespace std;
int main() {
    cout << "Calculator Program" << endl;
    // Add your calculator logic here
    return 0;
}'''
            if gui:
                skeleton_code += "\n// TODO: Add GUI code (Qt, GTK, etc.)"

        elif language_lower == "c":
            ext = "c"
            skeleton_code = '''#include <stdio.h>
int main() {
    printf("Calculator Program\\n");
    // Add your calculator logic here
    return 0;
}'''
            if gui:
                skeleton_code += "\n// TODO: Add GUI code (GTK+ or ncurses)"

        elif language_lower == "python":
            ext = "py"
            skeleton_code = 'print("Calculator Program")\n# Add your calculator logic here\n'
            if gui:
                skeleton_code += "# TODO: Add GUI (Tkinter, PyQt)"

        elif language_lower == "java":
            ext = "java"
            skeleton_code = f'''public class {project_name} {{
    public static void main(String[] args) {{
        System.out.println("Calculator Program");
        // Add your calculator logic here
    }}
}}'''
            if gui:
                skeleton_code += "\n// TODO: Add GUI (Swing, JavaFX)"

        else:
            return f"✅ Created folder '{project_name}' at {base} (language '{language}' not recognized)"

        filename = f"main.{ext}"
        filepath = os.path.join(base, filename)

        with open(filepath, 'w') as f:
            f.write(skeleton_code)

        return f"✅ Project '{project_name}' created with {language} skeleton at {base}"

    except Exception as e:
        return f"❌ Project creation error: {e}"


def do_create_file(folder_path, filename, content=None):
    try:
        folder_path = os.path.expanduser(folder_path or "~")
        Path(folder_path).mkdir(parents=True, exist_ok=True)

        file_path = os.path.join(folder_path, filename)

        # Open in write mode to overwrite or create new
        with open(file_path, "w") as f:
            if content is not None:
                f.write(content)
            else:
                # If no content provided, leave empty file
                pass
        
        return f"✅ File '{filename}' created/overwritten at: {file_path}"
    except Exception as e:
        return f"❌ Could not create or write file: {e}"
    
def get_code_for_file(purpose, language="c"):
    prompt = f"Write a complete {language} program for this purpose:\n\n{purpose}"
    return get_llm_response(prompt, code_only=True)

def do_file_exists(filename, type="any"):
    resolved_path = fuzzy_find_path(filename)
    if resolved_path and os.path.exists(resolved_path):
        item_type = "folder" if os.path.isdir(resolved_path) else "file"
        if type != "any" and type != item_type:
            return f"❌ '{filename}' exists but is not a {type}."
        return f"✅ Yes, {item_type} found: {resolved_path}"
    return f"❌ No, '{filename}' does not exist in your home directory."



def do_get_system_usage():
    """Fetches real-time CPU and RAM usage."""
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    return f"💻 CPU Usage: {cpu_usage}%\n🧠 RAM Usage: {ram_usage}% ({ram.used/1024**3:.2f}GB / {ram.total/1024**3:.2f}GB)"

def do_get_network_info():
    """Fetches IPv4 and IPv6 addresses for all network interfaces."""
    addrs = psutil.net_if_addrs()
    info = "🌐 Network Information:\n"
    for interface, addresses in addrs.items():
        ipv4 = next((addr.address for addr in addresses if addr.family == psutil.AF_INET), "N/A")
        ipv6 = next((addr.address for addr in addresses if addr.family == psutil.AF_INET6), "N/A")
        if ipv4 != "N/A" or ipv6 != "N/A":
            info += f"- {interface}:\n  - IPv4: {ipv4}\n  - IPv6: {ipv6}\n"
    return info
import os
import subprocess
import time
from mimetypes import guess_type

def do_change_wallpaper(image_path):
    """Changes the desktop wallpaper for KDE Plasma."""
    try:
        expanded_path = os.path.expanduser(image_path or "")
        if not expanded_path or not os.path.exists(expanded_path):
            return f"❌ Image file not found at: {expanded_path if expanded_path else '(no path provided)'}"

        # Validate image type
        mime, _ = guess_type(expanded_path)
        if not (mime and mime.startswith("image/")):
            return f"❌ Not an image: {expanded_path}"

        # KDE Plasma script (dbus-ksmserver/plasmashell)
        jscript = f"""
var allDesktops = desktops();
for (var i=0; i<allDesktops.length; i++) {{
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper","org.kde.image","General");
    d.writeConfig("Image", "file://{expanded_path}");
}}
"""

        # Try qdbus org.kde.plasmashell eval
        try:
            subprocess.run(
                ["qdbus-qt5", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", jscript],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return f"✅ Wallpaper changed to: {expanded_path}"
        except FileNotFoundError:
            # Fallback to qdbus (without -qt5) or dbus-send
            try:
                subprocess.run(
                    ["qdbus", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", jscript],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                return f"✅ Wallpaper changed to: {expanded_path}"
            except Exception as e:
                # As last resort, try plasmashell --replace (not ideal, but attempt)
                return f"❌ Failed to set wallpaper via qdbus: {e}"

    except Exception as e:
        return f"❌ Error changing wallpaper: {e}"
def find_first_image_in_folder(folder_path):
    try:
        folder_path = os.path.expanduser(folder_path)
        if not os.path.isdir(folder_path):
            return None
        exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        # Search immediate folder
        for name in sorted(os.listdir(folder_path)):
            p = os.path.join(folder_path, name)
            if os.path.isfile(p) and name.lower().endswith(exts):
                return p
        # Optionally, search subfolders if desired:
        # for root, dirs, files in os.walk(folder_path):
        #     for f in sorted(files):
        #         if f.lower().endswith(exts):
        #             return os.path.join(root, f)
        return None
    except Exception:
        return None


import os
import time
from mimetypes import guess_type

def dynamic_wallpaper_changer(folder_path, interval_seconds):
    # Validate interval
    try:
        interval = float(interval_seconds)
        if interval <= 0:
            print("❌ interval_seconds must be > 0")
            return
    except Exception:
        print("❌ interval_seconds must be a number")
        return

    # Resolve and validate folder
    folder_path = os.path.expanduser(folder_path or "")
    if not folder_path or not os.path.isdir(folder_path):
        print("❌ Provided path is not a directory")
        return

    def load_wallpapers():
        images = []
        try:
            for name in os.listdir(folder_path):
                # skip hidden files and temp files
                if name.startswith("."):
                    continue
                fp = os.path.join(folder_path, name)
                if not os.path.isfile(fp):
                    continue
                mime_type, _ = guess_type(fp)
                if mime_type and mime_type.startswith("image/"):
                    # ensure readable
                    if os.access(fp, os.R_OK):
                        images.append(fp)
        except Exception as e:
            print(f"❌ Error reading directory: {e}")
        images.sort()  # deterministic order
        return images

    wallpapers = load_wallpapers()
    if not wallpapers:
        print("❌ No wallpaper images found in the directory")
        return

    idx = 0
    print(f"🖼️ Loaded {len(wallpapers)} wallpapers from {folder_path}")
    try:
        while True:
            current = wallpapers[idx]
            try:
                # Attempt to set wallpaper
                do_change_wallpaper(current)
                # Optional: log which image was set
                # print(f"✅ Set wallpaper: {os.path.basename(current)}")
            except Exception as e:
                # Skip this file and continue
                print(f"⚠️ Failed to set {current}: {e}")

            # Advance index
            idx = (idx + 1) % len(wallpapers)

            # Sleep with small increments so we can refresh list periodically
            slept = 0.0
            refresh_every = max(30.0, interval)  # refresh at least every 30s or at the given interval
            while slept < interval:
                time.sleep(min(1.0, interval - slept))
                slept += min(1.0, interval - slept)

            # Periodically refresh the file list in case folder contents changed
            # Reload when we’ve completed a full cycle or at refresh interval
            if idx == 0 or slept >= refresh_every:
                new_list = load_wallpapers()
                if new_list:
                    wallpapers = new_list
                    # Clamp idx to new list size
                    idx %= len(wallpapers)
                else:
                    print("⚠️ No images found on refresh; keeping previous list.")
    except KeyboardInterrupt:
        print("\n🛑 Stopped wallpaper rotation.")

# Note for GNOME users: The command would be different, for example:
# gsettings set org.gnome.desktop.background picture-uri file:///path/to/image.jpg
import os

def do_rename_file(old_name, new_name, location=None):
    # Base directory = home by default
    base_dir = os.path.expanduser("~")

    # Map common location keywords
    location_map = {
        "desktop": "Desktop",
        "pictures": "Pictures",
        "documents": "Documents",
        "downloads": "Downloads",
        "music": "Music",
        "videos": "Videos"
    }

    # Override base_dir if location provided
    if location and location.lower() in location_map:
        base_dir = os.path.join(base_dir, location_map[location.lower()])

    # Build absolute paths
    old_path = os.path.join(base_dir, old_name)
    new_path = os.path.join(base_dir, new_name)

    # Check if target exists
    if not os.path.exists(old_path):
        return f"❌ File or folder not found: '{old_path}'"

    try:
        os.rename(old_path, new_path)
        item_type = "folder" if os.path.isdir(new_path) else "file"
        return f"✅ Successfully renamed {item_type} '{old_name}' to '{new_name}' in {base_dir}"
    except Exception as e:
        return f"❌ Rename failed: {e}"

def do_wifi_status():
    try:
        ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
        return f"📶 Connected to WiFi: {ssid}" if ssid else "❌ Not connected to any WiFi."
    except:
        return "❌ Could not fetch WiFi details."


def do_open_file(filename):
    try:
        resolved_path = fuzzy_find_path(filename)
        if not resolved_path or not os.path.isfile(resolved_path):
            return f"❌ File '{filename}' not found."
        subprocess.Popen(['xdg-open', resolved_path])
        return f"✅ File opened: {resolved_path}"
    except Exception as e:
        return f"❌ Error opening file: {e}"


def do_play_music(song):
    import urllib.parse
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(song)}"
    try:
        html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
        ids = re.findall(r"watch\?v=(\w{11})", html)
        if not ids or not isinstance(ids[0], str):
            return f"❌ No YouTube video found for '{song}'."
        video_url = f"https://www.youtube.com/watch?v={ids[0]}"

        webbrowser.open(video_url)
        return f"✅ Playing '{song}' on YouTube."
    except Exception as e:
        return f"❌ Failed to play song: {e}"

def do_stop_music():
    os.system("pkill -f 'brave|firefox|chrome|chromium'")
    return "✅ Stopped browser music (browser killed)."

def do_control_media(cmd):
    try:
        subprocess.run(['playerctl', cmd])
        return f"Media {cmd} executed."
    except Exception as e:
        return f"❌ Failed: {e}"

def do_change_brightness(amount: int):
    try:
        current = int(subprocess.check_output(['brightnessctl', 'g']).decode().strip())
        max_val = int(subprocess.check_output(['brightnessctl', 'm']).decode().strip())
        new = max(1, min(max_val, current + int((amount/100)*max_val)))
        subprocess.run(['brightnessctl', 's', str(new)])
        return f"✅ Brightness adjusted by {amount}%."
    except Exception as e:
        return f"❌ Failed to change brightness: {e}"
def do_delete_file(filepath):
    try:
        resolved_path = fuzzy_find_path(filepath)
        if not resolved_path or not os.path.isfile(resolved_path):
            return f"❌ File not found: {filepath}"
        os.remove(resolved_path)
        return f"✅ Successfully deleted file: {resolved_path}"
    except Exception as e:
        return f"❌ Error deleting file: {e}"


        filepath = filepath.replace("/home/user", "~")
        if filepath.startswith("/"):
            filepath = "~" + filepath.lstrip("/")  # /Music → ~/Music

        expanded_path = os.path.expanduser(filepath)
        if not os.path.exists(expanded_path):
            return f"❌ File not found at: {expanded_path}"

        os.remove(expanded_path)
        return f"✅ Successfully deleted file: {expanded_path}"

    except Exception as e:
        return f"❌ Error deleting file: {e}"



def do_open_browser():
    webbrowser.open("https://google.com")
    return "✅ Browser opened."

def speak_response(text: str):
    try:
        # Generate speech
        tts = gTTS(text=text, lang='en')
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        tts.save(temp_path)

        # Play the audio
        playsound.playsound(temp_path)

        # Remove the temp file
        os.remove(temp_path)

    except Exception as e:
        print(f"❌ TTS Error: {e}")

def do_navigate_to(url):
    webbrowser.open(url)
    return f"✅ Navigating to {url}"

def do_search_website(query):
    url = f"https://www.google.com/search?q={query.replace(' ','+')}"
    webbrowser.open(url)
    return f"✅ Searching: {query}"

def send_whatsapp_message(contact_name, message):
    driver = start_driver()
    wait = WebDriverWait(driver, 30)
    driver.get("https://web.whatsapp.com")

    try:
        # Wait for chat list to load
        chat_list_selectors = [
            '//div[@role="grid"]',
            '//div[@data-testid="chat-list"]'
        ]
        if not brute_force_find_element(driver, chat_list_selectors):
            raise Exception("WhatsApp Web chat list did not load.")

        # Locate search box
        search_box_selectors = [
            '//div[@contenteditable="true" and contains(@aria-label,"Search")]',
            '//div[@role="search"]//div[@contenteditable="true"]'
        ]
        search = brute_force_find_element(driver, search_box_selectors, clickable=True)
        if not search:
            raise Exception("Could not find the search box.")

        # Search for contact
        search.click()
        time.sleep(0.2)
        search.send_keys(Keys.CONTROL + "a", Keys.DELETE)
        search.send_keys(contact_name)
        time.sleep(1.0)  # Let results load

        # --- Brute force clickable rows after search ---
      # Scope search to chat list only
        row_selectors = [
    '//div[@role="grid"]//div[@data-testid="cell-frame-container"]',
    '//div[@role="grid"]//div[contains(@aria-label, "Chat with")]',
    '//div[@role="grid"]//div[@role="option"]',
    '//div[@role="grid"]//li[@role="listitem"]',
    '//div[@role="grid"]//div[@tabindex="0"]',
    '//div[@role="grid"]//div[contains(@class, "_ak8q")]'
    ]

        rows = []
        for xpath in row_selectors:
            try:
                found = driver.find_elements(By.XPATH, xpath)
                if found:
                    rows.extend(found)
            except:
                continue

        # Remove duplicates but keep order
        seen = set()
        unique_rows = []
        for r in rows:
            if r not in seen:
                unique_rows.append(r)
                seen.add(r)

        if not unique_rows:
            raise Exception("No search result rows found. Is the contact name correct?")

        # Click first row
        first_row = unique_rows[0]
        time.sleep(0.5)  # Let UI settle
        try:
            first_row.click()
        except:
            driver.execute_script("arguments[0].click();", first_row)

        time.sleep(0.6)

        # Message input box
        input_selectors = [
            '//footer//div[@contenteditable="true"]',
            '//div[@contenteditable="true" and @data-tab="10"]'
        ]
        input_box = brute_force_find_element(driver, input_selectors, clickable=True, timeout=8)
        if not input_box:
            raise Exception("Could not locate the message input box.")

        # Send the message
        input_box.click()
        time.sleep(0.2)
        input_box.send_keys(message)
        time.sleep(0.2)
        input_box.send_keys(Keys.ENTER)
        time.sleep(1)

        return f"✅ Message sent to '{contact_name}'."

    except Exception as e:
        try:
            with open("wa_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except:
            pass
        return f"❌ Failed to send message: {e}\n[Debug: see wa_debug.html]"
    finally:
        try:
            driver.quit()
        except:
            pass

import fitz  # PyMuPDF is already imported earlier


def do_process_document(file_path, query=None):
    """
    Processes a PDF, DOCX, or Image (JPEG/PNG) and returns either a summary or an answer in 50-60 lines or if user tells in short then short if user tell in long then long dynamically to a given query.
    """
    try:
        expanded_path = os.path.expanduser(file_path)
        if not os.path.exists(expanded_path):
            return f"❌ File not found: {expanded_path}"

        ext = os.path.splitext(expanded_path)[1].lower()
        extracted_text = ""

        # PDF
        if ext == ".pdf":
            import fitz  # PyMuPDF
            with fitz.open(expanded_path) as doc:
                for page in doc:
                    extracted_text += page.get_text()

        # DOCX
        elif ext == ".docx":
            import docx
            doc = docx.Document(expanded_path)
            extracted_text = "\n".join(p.text for p in doc.paragraphs)

        # Images (JPEG/PNG)
        elif ext in [".jpg", ".jpeg", ".png"]:
            from PIL import Image
            import pytesseract
            img = Image.open(expanded_path)
            extracted_text = pytesseract.image_to_string(img)

        else:
            return f"❌ Unsupported file type: {ext}"

        if not extracted_text.strip():
            return "❌ No text could be extracted from this file."

        extracted_text = extracted_text.strip()

        if not query:
            # If no query, summarize
            prompt = f"Summarize the following document in bullet points:\n\n{extracted_text[:5000]}"
        else:
            # If query provided, answer based on document
            prompt = f"The following document has this text:\n\n{extracted_text[:5000]}\n\nUser asks: {query}"

        response = get_llm_response(prompt, code_only=False)
        return response.strip()

    except Exception as e:
        return f"❌ Error processing document: {e}"

def do_send_whatsapp(contact, message):
    return send_whatsapp_message(contact, message)

def brute_force_find_element(driver, selectors, clickable=False, timeout=5):
    for xpath in selectors:
        try:
            if clickable:
                return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            else:
                return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception:
            continue
    return None

def brute_force_find_elements(driver, selectors, timeout=5):
    for xpath in selectors:
        try:
            elems = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            if elems:
                return elems
        except Exception:
            continue
    return None

    
def do_send_email(recipient, message):
    # Step 1 - Generate subject
    subject_prompt = f"Generate a short professional subject line for this email:\n\n{message}"
    subject = get_llm_response(subject_prompt, code_only=False)
    print(f"📌 Subject generated: {subject}")

    # Step 2 - Ask attachments
    attachments = []
    attach_input = input("📎 Any attachments? (Enter file paths separated by commas or 'no'): ").strip()
    if attach_input.lower() != "no" and attach_input:
        import os
        for path in attach_input.split(","):
            p = os.path.expanduser(path.strip())
            if os.path.isfile(p):
                attachments.append(p)
            else:
                print(f"❌ Not found: {p}")

    # Step 3 - Ask CC
    cc_list = []
    cc_input = input("👥 CC emails? (comma separated or 'no'): ").strip()
    if cc_input.lower() != "no" and cc_input:
        cc_list = [c.strip() for c in cc_input.split(",")]

    # Step 4 - AI-polished draft
    enhance_prompt = f"Rewrite the following email professionally:\n\n{message}"
    enhanced_message = get_llm_response(enhance_prompt, code_only=False)
    print("\n✍️ Enhanced draft:\n", enhanced_message)

    # Step 5 - Confirm send
    confirm = input("\n✅ Send this email? (yes/no): ").strip().lower()
    if confirm != "yes":
        return "❌ Email sending cancelled."

    # Step 6 - Send
    return send_email_with_attachments(recipient, cc_list, subject, enhanced_message, attachments)
def send_email_with_attachments(to_email, cc_emails, subject, body, attachments=None):
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None

    try:
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        service = build("gmail", "v1", credentials=creds)

        msg = EmailMessage()
        msg['To'] = to_email
        if cc_emails:
            msg['Cc'] = ", ".join(cc_emails)
        msg['Subject'] = subject
        msg.set_content(body)

        # Attach files if provided
        for file_path in attachments or []:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                maintype, subtype = mime_type.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"
            with open(file_path, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                                   filename=os.path.basename(file_path))

        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        return f"✅ Email sent to {to_email}."

    except Exception as e:
        return f"❌ Failed to send email: {e}"


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import shutil
import os

def start_driver():
    options = Options()
    options.binary_location = "/usr/bin/brave"

    
    options.add_argument("--user-data-dir=/home/anas/.config/BraveSoftware/AutomationProfile")

    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--remote-debugging-port=9222")  # helps with DevToolsActivePort
    
    # Remove automation flag
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    CHROMEDRIVER_PATH = shutil.which("chromedriver")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # Remove navigator.webdriver flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    return driver

def do_tell_time():
    return "⏰ " + datetime.now().strftime("%H:%M:%S")
import shutil
import os
from pathlib import Path

def do_move_file_folder(source_path, destination_path):
    try:
        src = os.path.expanduser(source_path)
        dst = os.path.expanduser(destination_path)

        if not os.path.exists(src):
            return f"❌ Source '{src}' does not exist."

        # Create destination if doesn't exist
        if not os.path.exists(dst):
            Path(dst).mkdir(parents=True, exist_ok=True)

        # If destination is a dir, keep filename/folder name same
        if os.path.isdir(dst):
            final_dst = os.path.join(dst, os.path.basename(src))
        else:
            final_dst = dst

        shutil.move(src, final_dst)
        return f"✅ Moved '{src}' to '{final_dst}'."
    except Exception as e:
        return f"❌ Failed to move: {e}"


def do_tell_date():
    return "📆 " + datetime.now().strftime("%A, %d %B %Y")

def do_announce(message):
    try:
        subprocess.run(['espeak', message])
    except:
        pass
    return f"[Speak]: {message}"

def do_system_info():
    uname = platform.uname()
    ram_gb = round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3), 2)
    return f"{uname.system} {uname.release} on {uname.node}. CPU: {uname.processor}. RAM: {ram_gb} GB"

def do_battery_status():
    try:
        import psutil
        b = psutil.sensors_battery()
        return f"🔋 {b.percent}% {'charging' if b.power_plugged else 'discharging'}"
    except:
        return "🔋 Battery status not available."
def do_wifi_status():
    try:
        ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
        return f"📶 Connected to WiFi: {ssid}" if ssid else "❌ Not connected to any WiFi."
    except:
        return "❌ Could not fetch WiFi details."
def do_bluetooth_devices():
    try:
        output = subprocess.check_output("bluetoothctl paired-devices", shell=True).decode().strip()
        return f"🔵 Paired Bluetooth Devices:\n{output}" if output else "🔵 No Bluetooth devices paired."
    except:
        return "❌ Could not get Bluetooth devices."
def do_connected_devices():
    try:
        out = subprocess.check_output("lsusb", shell=True).decode()
        return f"🖱️ Connected USB Devices:\n{out}"
    except:
        return "❌ Failed to fetch USB devices."
def do_general_knowledge(question):
    prompt = f"Answer concisely:\n\n{question}"
    return get_llm_response(prompt)

def generate_code_content(filename, purpose="calculator"):
    ext = os.path.splitext(filename)[1].lower()
    lang = {
        ".c": "C",
        ".cpp": "C++",
        ".py": "Python",
        ".java": "Java"
    }.get(ext, "C")

    prompt = f"Write a complete {lang} program for a basic {purpose}."
    return get_llm_response(prompt, code_only=True)


def do_chat(resp):
    return resp

def do_extract_pdf_text(query):
    try:
        url = subprocess.check_output([
            "qdbus", "org.kde.okular", "/okular", "org.kde.okular.getDocumentUrl"
        ]).decode().strip()
        if not url.startswith("file://"):
            return "❌ No PDF open in Okular."
        filepath = url.replace("file://", "")
        pdf_text = subprocess.check_output(["pdftotext", filepath, "-"]).decode()
        if not query:
            return "📄 PDF content:\n" + pdf_text[:1500]
        else:
            prompt = f"The PDF loaded in Okular has this content:\n\n{pdf_text[:5000]}\n\nUser asks: {query}"
            summary = get_llm_response(prompt, code_only=False)
            return summary
    except Exception as e:
        return f"❌ PDF extraction error: {e}"

action_mapping = {
    "create_folder": lambda d: do_create_folder(
    d.get("folder_path"),
    d.get("filename")  # if present, it's the folder name
),
    "create_project": lambda d: do_create_project(d.get("project_name"), d.get("location"), d.get("language"), d.get("gui")),
    "create_file": lambda d: do_create_file(
    d.get("folder_path"),
    d.get("filename"),
    d.get("content") 
),
    "file_exists": lambda d: do_check_exists(d.get("filename"), d.get("type", "any")),

    "open_file": lambda d: do_open_file(d.get("filename")),
    "play_music": lambda d: do_play_music(d.get("song")),
    "process_document": lambda d: do_process_document(
    d.get("file_path"),
    d.get("query")
),

    "stop_music": lambda d: do_stop_music(),
    "next_music": lambda d: do_control_media("next"),
    "previous_music": lambda d: do_control_media("previous"),
    "fix_code": lambda d: do_fix_code(d.get("file_path")),
    "control_volume": lambda d: do_control_volume(d.get("amount", 0)),
    # "get_memory": lambda d: do_get_memory(),
    "remember_name": lambda d: do_remember_name(d.get("name")),
    "get_name": lambda d: do_get_name(),



    "search_web": lambda d: do_search_web(d.get("query")),
   # "`find_in_pd`": lambda d: find_text_in_pdf(d.get("file_path"), d.get("query")),
   #"find_in_pdf": lambda d: find_text_in_pdf(d.get("file_path"), d.get("query")),
    "open_browser": lambda d: do_open_browser(),
    "navigate_to": lambda d: do_navigate_to(d.get("url")),
    "search_website": lambda d: do_search_website(d.get("query")),
   "send_whatsapp": lambda d: send_whatsapp_message(start_driver(), d.get("contact"), d.get("message")),
    "system_usage": lambda d: do_get_system_usage(),
    "get_weather": lambda d: do_get_weather(d.get("city", "Nagpur")),
    "wifi_status": lambda d: do_wifi_status(),
    "bluetooth_devices": lambda d: do_bluetooth_devices(),
    "connected_devices": lambda d: do_connected_devices(),
    "general_knowledge": lambda d: do_search_web(d.get("question")),
    "save_note": lambda d: do_save_note(d.get("filename"), d.get("content")),
    "remind_me": lambda d: do_remind_me(d.get("message"), int(d.get("after_minutes", 5))),
    "trash_files": lambda d: do_trash_files(d.get("path_pattern")),
    "network_info": lambda d: do_get_network_info(),
    "move_file_folder": lambda d: do_move_file_folder(d.get("source_path"), d.get("destination_path")),

    "delete_file": lambda d: do_delete_file(d.get("filepath")),
    "change_wallpaper": lambda d: do_change_wallpaper(d.get("image_path")),
    "tell_time": lambda d: do_tell_time(),
    "tell_date": lambda d: do_tell_date(),
    "announce": lambda d: do_announce(d.get("message")),
    "network_info": lambda d: do_get_network_info(),
    "system_info": lambda d: do_system_info(),
    "battery_status": lambda d: do_battery_status(),
    "change_brightness": lambda d: do_change_brightness(int(d.get("amount", 0))),
    "extract_pdf_text": lambda d: do_extract_pdf_text(d.get("query")),
    "rename_file": lambda d: do_rename_file(d.get("filepath"), d.get("newname")),
    "chat": lambda d: do_chat(d.get("message")),
    "none": lambda d: "❌ Sorry, I could not understand your command.",
    "wifi_status": lambda d: do_wifi_status(),
    "list_dir_contents": lambda d: do_list_dir_contents(
    normalize_path(d.get("path", "")),
    #d.get("path"),
    d.get("type", "all")
),

"send_email": lambda d: do_send_email(
    d.get("recipient"),
    d.get("message")
),
}
def update_memory(user_message):
    memory_file = "memory.txt"
    lines = []
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            lines = f.readlines()  # purane commands load karo

    lines.append(user_message + "\n")  # naya command last me jodo

    if len(lines) > 20:  # agar 20 se zyada command hain
        lines = lines[-20:]  # sirf last 20 rakho

    with open(memory_file, "w", encoding="utf-8") as f:
        f.writelines(lines)  # file overwrite karo nayi list ke sath

def do_get_memory():
    """Returns the stored last commands from memory.txt."""
    memory_file = "memory.txt"
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                data = f.read().strip()
            return "📝 Previous commands:\n" + (data if data else "⚠️ No commands stored yet.")
        except Exception as e:
            return f"❌ Could not read memory: {e}"
    return "❌ No memory found."
def do_remember_name(name):
    """Store the user's name in memory.txt as a key-value."""
    memory_file = "memory.txt"
    # Store in simple format: NAME: Anas
    lines = []
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Remove old NAME entries
        lines = [l for l in lines if not l.startswith("NAME:")]
    lines.append(f"NAME:{name}\n")
    with open(memory_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return f"✅ Got it, {name}. I'll remember that."
def do_get_name():
    memory_file = "memory.txt"
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAME:"):
                    return f"Your name is {line.split(':',1)[1].strip()}."
    return "❌ I don't know your name yet."


def handle_intent(user_message):
    update_memory(user_message)

    # 🔹 Step 1: Resolve references before sending to LLM
    user_message = resolve_references_in_message(user_message)

    # 🔹 Step 2: Extract actions from LLM
    actions = extract_llm_intent(user_message)
    results = []

    for action in actions:
        # Store this action's details into context for future
        update_context_from_action(action)

        if action["action"] == "chat":
            resp = do_chat(action["message"])
            speak_response(resp)
            results.append(resp)
        else:
            handler = globals().get(f"do_{action['action']}")
            if callable(handler):
                try:
                    try:
                        handler_result = handler(**{k: v for k, v in action.items() if k != "action"})
                    except TypeError:
                        handler_result = handler(*[v for k, v in action.items() if k != "action"])
                except Exception as e:
                    handler_result = f"❌ Error: {e}"
            else:
                handler_result = "❌ Unknown action"

            speak_response(handler_result)
            results.append(handler_result)

    return results



def main():
    print("👿 Lucifer Agent Ready. Speak your command (type 'exit' or 'quit' to stop).")
    while True:
        try:
            q = input("👿 Command me: ").strip()
            if q.lower() in ("exit", "quit"):
                print("👿 Lucifer Agent terminated.")
                break
            if not q:
                continue
            if q.lower().startswith("pdf"):
                query = q[3:].strip()
                print(do_extract_pdf_text(query))
                continue
            result = handle_intent(q)
            print(result)
        except (KeyboardInterrupt, EOFError):
            print("\n👿 Agent interrupted.")
            break

if __name__ == "__main__":
    main()
