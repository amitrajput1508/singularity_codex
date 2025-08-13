import webview
import json
from backend import handle_intent
import speech_recognition as sr
import threading
import time
import sys

from gtts import gTTS
import tempfile
import os
from datetime import datetime
from pathlib import Path
import base64
import requests
from PIL import Image, ImageFilter
import mss
import subprocess

# Vision configuration
VISION_INTERVAL = 15  # seconds between screenshots
VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct"
VISION_API_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_API_KEY = "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"
VISION_OUTPUT_DIR = Path("screen_logs")
VISION_SCREENSHOT_DIR = VISION_OUTPUT_DIR / "screenshots"
VISION_LOG_FILE = VISION_OUTPUT_DIR / "descriptions.log"
DELETE_SCREENSHOT_AFTER_SEND = True
BLUR_SENSITIVE_REGION = False
SENSITIVE_BOX = None

# Create directories if they don't exist
VISION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VISION_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>👑 Lucifer AI - Premium Assistant</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f0c29;
            --card: #1a1a40;
            --accent: #8e2de2;
            --accent2: #4a00e0;
            --text: #f8f9fa;
            --muted: #adb5bd;
            --error: #ff4d4d;
            --success: #38b000;
            --warning: #ffaa00;
            --window-border: rgba(142, 45, 226, 0.3);
            --window-header: rgba(26, 26, 64, 0.9);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', 'Segoe UI', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, var(--bg), var(--card));
            color: var(--text);
            height: 100vh;
            overflow: hidde/home/anas/Desktop/test.cn;
            -webkit-app-region: drag;
        }
        
        /* Window Controls */
        .window-controls {
            position: fixed;
            top: 0;
            right: 0;
            display: flex;
            z-index: 9999;
            -webkit-app-region: no-drag;
        }
        
        .window-btn {
            width: 46px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .email-section {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 13px;
            color: var(--muted);
        }

        .form-input {
            width: 100%;
            padding: 8px 12px;
            border-radius: 6px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--text);
            font-size: 13px;
        }

        .form-input::placeholder {
            color: rgba(255,255,255,0.3);
        }

        .email-status {
            margin-top: 10px;
            padding: 8px;
            border-radius: 6px;
            font-size: 13px;
            display: none;
        }

        .email-status.success {
            background: rgba(56, 176, 0, 0.1);
            border-left: 3px solid var(--success);
            display: block;
        }

        .email-status.error {
            background: rgba(255, 77, 77, 0.1);
            border-left: 3px solid var(--error);
            display: block;
        }
        
        .window-btn:hover {
            background: rgba(255,255,255,0.1);
            color: var(--text);
        }
        
        .window-btn.close:hover {
            background: #e81123;
            color: white;
        }
        
        /* Main App Container */
        .app-container {
            display: flex;
            height: 100vh;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--window-border);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .message {
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 14px;
            line-height: 1.3;
            font-size: 14px;
            word-wrap: break-word;
            position: relative;
            animation: fadeIn 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* User messages */
        .message.user {
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
            max-width: 85%;
        }

        /* Bot messages */
        .message.bot {
            background: rgba(26, 26, 64, 0.9);
            color: var(--text);
            margin-right: auto;
            border-bottom-left-radius: 4px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* Welcome message specific styling */
        .message.welcome {
            max-width: 120%;
            padding: px;
            margin: 10px auto;
            border-radius: 12px;
            background: rgba(26, 26, 64, 0.9);
            border: 1px solid var(--accent);
            text-align: center;
        }

        /* Vision messages */
        .message.vision {
            background: rgba(255, 170, 0, 0.08);
            border-left: 3px solid var(--warning);
            padding: 10px 12px;
        }

        /* Small messages styling */
        .message[data-small="true"] {
            padding: 8px 12px;
            font-size: 13px;
            max-width: 60%;
        }

        /* Medium messages styling */
        .message[data-medium="true"] {
            max-width: 70%;
        }

        /* Animation for message appearance */
        @keyframes fadeIn {
            from { 
                opacity: 0;
                transform: translateY(5px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: rgba(26, 26, 64, 0.8);
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        /* Welcome Message Styles */
        .message.welcome {
            max-width: 80%;
            margin: 20px auto;
            padding: 20px;
            border-radius: 12px;
            background: rgba(26, 26, 64, 0.8);
            border: 1px solid var(--accent);
            text-align: center;
            animation: fadeInUp 0.8s ease;
        }
        
        /* Typing indicator styles */
        .typing-indicator {
            display: inline-flex;
            align-items: center;
            padding: 8px 12px;
            background: rgba(26, 26, 64, 0.8);
            border-radius: 18px;
            margin-right: auto;
            min-width: 80px;
            border: 1px solid rgba(255,255,255,0.1);
            box-sizing: border-box;
        }

        .typing-content {
            display: flex;
            align-items: center;
            width: 100%;
        }

        .typing-dots {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            margin: 0 2px;
            animation: typingAnimation 1.4s infinite ease-in-out;
            flex-shrink: 0;
        }

        .typing-dot:nth-child(1) {
            animation-delay: 0s;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typingAnimation {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-5px); }
        }

        .typing-text {
            color: var(--muted);
            font-size: 12px;
            margin-left: 8px;
            font-style: italic;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex-shrink: 1;
        }

        .welcome-title {
            font-size: 20px;
            margin-bottom: 15px;
            background: linear-gradient(to right, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .welcome-images {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .welcome-image {
            width: 120px;
            height: 90px;
            border-radius: 8px;
            object-fit: cover;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            border: 1px solid rgba(142, 45, 226, 0.3);
            opacity: 0;
            transform: translateY(20px);
        }
        
        .welcome-image:nth-child(1) {
            animation: fadeInUp 0.6s ease 0.3s forwards;
        }
        .welcome-image:nth-child(2) {
            animation: fadeInUp 0.6s ease 0.5s forwards;
        }
        .welcome-image:nth-child(3) {
            animation: fadeInUp 0.6s ease 0.7s forwards;
        }
        
        .welcome-image:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(142, 45, 226, 0.3);
        }
        
        .welcome-text {
            color: var(--muted);
            font-size: 14px;
            margin-top: 15px;
            animation: fadeIn 0.8s ease 1s both;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeInUp {
            from { 
                opacity: 0;
                transform: translateY(20px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .app-logo {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 0;
            margin-bottom: 20px;
        }
        
        .app-logo i {
            font-size: 28px;
            color: var(--accent);
        }
        
        .app-logo h1 {
            font-size: 22px;
            font-weight: 600;
            background: linear-gradient(to right, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Quick Actions */
        .section-title {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--muted);
            margin: 15px 0 10px 0;
        }
        
        .action-btn {
            width: 100%;
            padding: 12px 15px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .action-btn:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .action-btn i {
            font-size: 16px;
        }
        
        /* Vision Controls */
        .vision-controls {
            margin-top: auto;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .vision-toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255,255,255,0.1);
            transition: .4s;
            border-radius: 24px;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: var(--muted);
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: var(--accent);
        }
        
        input:checked + .slider:before {
            transform: translateX(26px);
            background-color: white;
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(15, 12, 41, 0.6);
        }
        
        .chat-header {
            padding: 15px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
        }
        
        .chat-title {
            font-size: 18px;
            font-weight: 500;
        }
        
        .status-indicator {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--muted);
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
        }
        
        .status-dot.listening {
            background: var(--accent);
            animation: pulse 1s infinite;
        }
        
        .status-dot.vision-active {
            background: var(--warning);
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .message {
            max-width: 80%;
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.4;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: white;
            margin-left: auto;
        }
        
        .message.bot {
            background: rgba(26, 26, 64, 0.8);
            color: var(--text);
            margin-right: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .message.vision {
            background: rgba(255, 170, 0, 0.1);
            border-left: 3px solid var(--warning);
        }
        
        /* Input Area */
        .input-container {
            padding: 15px 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            background: rgba(26, 26, 64, 0.8);
        }
        
        .input-box {
            display: flex;
            gap: 10px;
        }
        
        .input-wrapper {
            position: relative;
            flex: 1;
        }
        
        .text-input {
            width: 100%;
            min-height: 50px;
            max-height: 150px;
            padding: 12px 45px 12px 15px;
            border-radius: 8px;
            border: none;
            background: rgba(255,255,255,0.05);
            color: var(--text);
            font-size: 14px;
            resize: none;
            outline: none;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .voice-input-btn {
            position: absolute;
            right: 10px;
            bottom: 10px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: rgba(142, 45, 226, 0.2);
            border: none;
            color: var(--accent);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        
        .voice-input-btn:hover {
            background: rgba(142, 45, 226, 0.3);
        }
        
        .voice-input-btn.listening {
            background: var(--error);
            color: white;
            animation: pulse 1s infinite;
        }
        
        .send-btn {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Vision Preview */
        .vision-preview {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 200px;
            height: 120px;
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid var(--accent);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 100;
            display: none;
        }
        
        .vision-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .vision-preview.active {
            display: block;
        }
        
        /* Voice Modal */
        .voice-modal {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(26, 26, 64, 0.95);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            z-index: 100;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .voice-modal.active {
            opacity: 1;
            visibility: visible;
        }
        
        .voice-icon {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .voice-icon i {
            font-size: 24px;
            color: var(--accent);
        }
        
        .voice-text {
            font-size: 16px;
            font-weight: 500;
        }
        
        /* Settings Modal */
        .settings-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-width: 90%;
            background: rgba(26, 26, 64, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .settings-modal.active {
            opacity: 1;
            visibility: visible;
        }
        
        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .settings-title {
            font-size: 20px;
            font-weight: 600;
        }
        
        .close-settings {
            background: none;
            border: none;
            color: var(--muted);
            font-size: 20px;
            cursor: pointer;
        }
        
        .settings-section {
            margin-bottom: 20px;
        }
        
        .settings-section-title {
            font-size: 16px;
            margin-bottom: 10px;
            color: var(--accent);
        }
        
        .settings-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .settings-label {
            font-size: 14px;
        }
        
        .settings-input {
            width: 100px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            color: var(--text);
        }
        
        .settings-btn {
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .settings-btn:hover {
            background: var(--accent2);
        }
        
        /* Vision Settings Modal */
        .settings-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-width: 90%;
            background: rgba(26, 26, 64, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .settings-modal.active {
            opacity: 1;
            visibility: visible;
        }
        
        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .settings-title {
            font-size: 20px;
            font-weight: 600;
        }
        
        .close-settings {
            background: none;
            border: none;
            color: var(--muted);
            font-size: 20px;
            cursor: pointer;
        }
        
        .settings-section {
            margin-bottom: 20px;
        }
        
        .settings-section-title {
            font-size: 16px;
            margin-bottom: 10px;
            color: var(--accent);
        }
        
        .settings-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .settings-label {
            font-size: 14px;
        }
        
        .settings-input {
            width: 100px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            color: var(--text);
        }
        
        .settings-btn {
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .settings-btn:hover {
            background: var(--accent2);
        }
        
        /* Overlay */
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
            z-index: 999;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .overlay.active {
            opacity: 1;
            visibility: visible;
        }

        /* Email Modal */
        .email-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-width: 90%;
            background: rgba(26, 26, 64, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }

        .email-modal.active {
            opacity: 1;
            visibility: visible;
        }

        .email-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .close-email {
            background: none;
            border: none;
            color: var(--muted);
            font-size: 20px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <!-- Window Controls -->
    <div class="window-controls">
        <div class="window-btn" id="minimize-btn">
            <i class="fas fa-minus"></i>
        </div>
        <div class="window-btn" id="maximize-btn">
            <i class="far fa-square"></i>
        </div>
        <div class="window-btn close" id="close-btn">
            <i class="fas fa-times"></i>
        </div>
    </div>
    
    <!-- Main App -->
    <div class="app-container" id="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="app-logo">
                <i class="fas fa-robot"></i>
                <h1 style="font-family: 'Poppins', sans-serif; font-size: 48px; font-weight: 700; letter-spacing: 2px; color: #8e2de2; text-align: center;">
                    Zuno
                </h1>
            </div>
            
            <div class="quick-actions">
                <div class="section-title">Quick Actions</div>
                <button class="action-btn" id="voice-btn">
                    <i class="fas fa-microphone"></i>
                    <span>Voice Command</span>
                </button>
                <button class="action-btn" id="analyze-screen-btn">
                    <i class="fas fa-desktop"></i>
                    <span>Analyze Screen</span>
                </button>
                <button class="action-btn" id="settings-btn">
                    <i class="fas fa-cog"></i>
                    <span>Settings</span>
                </button>
            </div>
            
            <div class="vision-controls">
                <div class="section-title">Vision Controls</div>
                <div class="vision-toggle">
                    <span>Screen Analysis</span>
                    <label class="toggle-switch">
                        <input type="checkbox" id="vision-toggle">
                        <span class="slider"></span>
                    </label>
                </div>
                <button class="action-btn" id="vision-settings-btn">
                    <i class="fas fa-sliders-h"></i>
                    <span>Vision Settings</span>
                </button>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <div class="chat-header">
                <h2 class="chat-title">AI Assistant</h2>
                <div class="status-indicator">
                    <div class="status-dot" id="status-dot"></div>
                    <span id="status-text">Ready</span>
                </div>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message bot welcome" id="welcome-message"
                    style="padding: 40px; 
                            background: rgba(255, 255, 255, 0.15); 
                            backdrop-filter: blur(10px); 
                            -webkit-backdrop-filter: blur(10px);
                            border-radius: 25px;
                            font-size: 20px; 
                            width: 90%; 
                            max-width: 900px; 
                            margin-top: 40px;
                            margin: 30px auto;
                            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25); 
                            border: 1px solid rgba(255, 255, 255, 0.18);">

                    <div class="welcome-title" 
                        style="font-size: 32px; font-weight: bold; text-align: center; margin-bottom: 30px;">
                        ✨👁️‍🗨️ Welcome to <span style="color: #8e2de2;">Zuno</span> AI Agent ⚡🤖
                    </div>

                    <div class="welcome-text" 
                        style="text-align: center; font-size: 24px; font-weight: 500;">
                        How can I help you today?
                    </div>
                </div>
            </div>
            
            <div class="input-container">
                <div class="input-box">
                    <div class="input-wrapper">
                        <textarea class="text-input" id="text-input" placeholder="Ask Lucifer anything..." rows="1"></textarea>
                        <button class="voice-input-btn" id="voice-input-btn">
                            <i class="fas fa-microphone"></i>
                        </button>
                    </div>
                    <button class="send-btn" id="send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Vision Preview -->
    <div class="vision-preview" id="vision-preview">
        <img id="vision-preview-img" src="">
    </div>
    
    <!-- Voice Recognition Modal -->
    <div class="voice-modal" id="voice-modal">
        <div class="voice-icon">
            <i class="fas fa-microphone"></i>
        </div>
        <div class="voice-text" id="voice-text">Listening...</div>
    </div>
    
    <!-- Settings Modal -->
    <div class="settings-modal" id="settings-modal">
        <div class="settings-header">
            <h3 class="settings-title">Settings</h3>
            <button class="close-settings" id="close-settings-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="settings-section">
            <h4 class="settings-section-title">General</h4>
            <div class="settings-row">
                <span class="settings-label">Theme</span>
                <select class="settings-input" id="theme-select">
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="system">System</option>
                </select>
            </div>
        </div>
        
        <div class="settings-section">
            <h4 class="settings-section-title">Voice</h4>
            <div class="settings-row">
                <span class="settings-label">Voice Speed</span>
                <input type="range" class="settings-input" id="voice-speed" min="0.5" max="2" step="0.1" value="1">
            </div>
        </div>
        
        <button class="settings-btn" id="save-settings-btn">Save Settings</button>
    </div>
    
    <!-- Vision Settings Modal -->
    <div class="settings-modal" id="vision-settings-modal">
        <div class="settings-header">
            <h3 class="settings-title">Vision Settings</h3>
            <button class="close-settings" id="close-vision-settings-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="settings-section">
            <h4 class="settings-section-title">Screen Analysis</h4>
            <div class="settings-row">
                <span class="settings-label">Interval (seconds)</span>
                <input type="number" class="settings-input" id="vision-interval" min="5" max="300" value="15">
            </div>
            <div class="settings-row">
                <span class="settings-label">Blur Sensitive Area</span>
                <label class="toggle-switch">
                    <input type="checkbox" id="vision-blur-toggle">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        
        <button class="settings-btn" id="save-vision-settings-btn">Save Settings</button>
    </div>

    <!-- Email Modal -->
    <div class="email-modal" id="email-modal">
        <div class="email-header">
            <h3>Send Email</h3>
            <button class="close-email" id="close-email-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="email-section">
            <div class="form-group">
                <label>To:</label>
                <input type="text" class="form-input" id="email-recipient" placeholder="recipient@example.com">
            </div>
            
            <div class="form-group">
                <label>Subject:</label>
                <input type="text" class="form-input" id="email-subject" placeholder="Subject">
            </div>
            
            <div class="form-group">
                <label>Message:</label>
                <textarea class="form-input" id="email-message" rows="5"></textarea>
            </div>
            
            <div class="form-group">
                <label>Attachments (comma separated paths):</label>
                <input type="text" class="form-input" id="email-attachments" placeholder="~/file1.txt, ~/image.jpg">
            </div>
            
            <div class="form-group">
                <label>CC (comma separated emails):</label>
                <input type="text" class="form-input" id="email-cc" placeholder="cc1@example.com, cc2@example.com">
            </div>
            
            <div class="email-status" id="email-status"></div>
        </div>
        
        <button class="settings-btn" id="send-email-btn">Send Email</button>
    </div>
    
    <!-- Overlay -->
    <div class="overlay" id="overlay"></div>

    <script>
        // DOM Elements
        const chatMessages = document.getElementById('chat-messages');
        const textInput = document.getElementById('text-input');
        const sendBtn = document.getElementById('send-btn');
        const voiceInputBtn = document.getElementById('voice-input-btn');
        const voiceModal = document.getElementById('voice-modal');
        const voiceText = document.getElementById('voice-text');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const minimizeBtn = document.getElementById('minimize-btn');
        const maximizeBtn = document.getElementById('maximize-btn');
        const closeBtn = document.getElementById('close-btn');
        const visionToggle = document.getElementById('vision-toggle');
        const visionPreview = document.getElementById('vision-preview');
        const visionPreviewImg = document.getElementById('vision-preview-img');
        const analyzeScreenBtn = document.getElementById('analyze-screen-btn');
        const settingsBtn = document.getElementById('settings-btn');
        const settingsModal = document.getElementById('settings-modal');
        const closeSettingsBtn = document.getElementById('close-settings-btn');
        const saveSettingsBtn = document.getElementById('save-settings-btn');
        const visionSettingsBtn = document.getElementById('vision-settings-btn');
        const visionSettingsModal = document.getElementById('vision-settings-modal');
        const closeVisionSettingsBtn = document.getElementById('close-vision-settings-btn');
        const saveVisionSettingsBtn = document.getElementById('save-vision-settings-btn');
        const overlay = document.getElementById('overlay');
        const visionIntervalInput = document.getElementById('vision-interval');
        const visionBlurToggle = document.getElementById('vision-blur-toggle');
        
        // Email Modal Elements
        const emailModal = document.getElementById('email-modal');
        const closeEmailBtn = document.getElementById('close-email-btn');
        const sendEmailBtn = document.getElementById('send-email-btn');
        const emailRecipient = document.getElementById('email-recipient');
        const emailSubject = document.getElementById('email-subject');
        const emailMessage = document.getElementById('email-message');
        const emailAttachments = document.getElementById('email-attachments');
        const emailCC = document.getElementById('email-cc');
        const emailStatus = document.getElementById('email-status');
        
        // State
        let isListening = false;
        let isMaximized = false;
        let isVisionActive = false;
        let visionInterval = 15;
        let visionTimer = null;
        
        // Initialize
        function init() {
            setupEventListeners();
            loadSettings();
            
            // Speak welcome message
            setTimeout(() => {
                speak("Welcome to zuno ai agen. How can I help you today?");
            }, 1000);
        }
        
        function setupEventListeners() {
            // Text input
            textInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = `${this.scrollHeight}px`;
            });
            
            textInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Buttons
            sendBtn.addEventListener('click', sendMessage);
            voiceInputBtn.addEventListener('click', toggleVoiceRecognition);
            analyzeScreenBtn.addEventListener('click', analyzeScreen);
            
            // Window controls
            minimizeBtn.addEventListener('click', () => {
                window.pywebview.api.minimize_window();
            });
            
            maximizeBtn.addEventListener('click', () => {
                if (isMaximized) {
                    window.pywebview.api.restore_window();
                    maximizeBtn.innerHTML = '<i class="far fa-square"></i>';
                } else {
                    window.pywebview.api.maximize_window();
                    maximizeBtn.innerHTML = '<i class="far fa-window-restore"></i>';
                }
                isMaximized = !isMaximized;
            });
            
            closeBtn.addEventListener('click', () => {
                window.pywebview.api.close_window();
            });
            
            // Vision toggle
            visionToggle.addEventListener('change', toggleVision);
            
            // Settings
            settingsBtn.addEventListener('click', openSettings);
            closeSettingsBtn.addEventListener('click', closeSettings);
            saveSettingsBtn.addEventListener('click', saveSettings);
            
            // Vision settings
            visionSettingsBtn.addEventListener('click', openVisionSettings);
            closeVisionSettingsBtn.addEventListener('click', closeVisionSettings);
            saveVisionSettingsBtn.addEventListener('click', saveVisionSettings);
            
            // Email controls
            closeEmailBtn.addEventListener('click', closeEmailModal);
            sendEmailBtn.addEventListener('click', sendEmail);
            
            // Overlay
            overlay.addEventListener('click', () => {
                closeSettings();
                closeVisionSettings();
                closeEmailModal();
            });
        }
        
        function addWelcomeMessage() {
            speak("Hello! I'm Lucifer, your AI assistant. How can I help you today?");
        }
        
        function speak(text) {
            window.pywebview.api.speak(text);
        }
        
        function addMessage(text, sender, type = 'normal') {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${sender}`;
            if (type === 'vision') {
                messageEl.classList.add('vision');
            }
            messageEl.textContent = text;
            chatMessages.appendChild(messageEl);
            scrollToBottom();
        }
        
        function showTyping(status = "Typing...") {
            // Remove existing typing indicator if any
            hideTyping();
            
            const typingEl = document.createElement('div');
            typingEl.className = 'message bot';
            typingEl.id = 'typing-indicator';
            
            typingEl.innerHTML = `
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <span class="typing-text">${status}</span>
                </div>
            `;
            
            chatMessages.appendChild(typingEl);
            scrollToBottom();
            
            // Update status indicator
            statusDot.classList.add('typing');
            statusText.textContent = status;
        }
        
        function hideTyping() {
            const existingTyping = document.getElementById('typing-indicator');
            if (existingTyping) {
                existingTyping.remove();
            }
            statusDot.classList.remove('typing');
            statusText.textContent = 'Ready';
        }
        
        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function toggleVoiceRecognition() {
            if (!isListening) {
                startVoiceRecognition();
            } else {
                stopVoiceRecognition();
            }
        }
        
        function startVoiceRecognition() {
            isListening = true;
            voiceInputBtn.classList.add('listening');
            voiceModal.classList.add('active');
            statusDot.classList.add('listening');
            statusText.textContent = 'Listening...';
            
            window.pywebview.api.start_listening().then((result) => {
                if (result && typeof result === 'string' && result.trim().length > 0) {
                    textInput.value = result;
                    sendMessage();
                }
                stopVoiceRecognition();
            });
        }
        
        function stopVoiceRecognition() {
            isListening = false;
            voiceInputBtn.classList.remove('listening');
            voiceModal.classList.remove('active');
            statusDot.classList.remove('listening');
            statusText.textContent = 'Ready';
        }
        
        async function sendMessage() {
            const text = textInput.value.trim();
            if (!text) return;
            
            hideWelcomeMessage();
            addMessage(text, 'user');
            textInput.value = '';
            textInput.style.height = 'auto';
            
            // Check if this is an email command
            if (text.toLowerCase().includes('send email') || 
                text.toLowerCase().includes('mail') ||
                text.toLowerCase().includes('email')) {
                
                // Extract recipient and message if possible
                const recipientMatch = text.match(/(?:to|send)\s+([^\s@]+@[^\s@]+\.[^\s@]+)/i);
                const recipient = recipientMatch ? recipientMatch[1] : '';
                
                const messageMatch = text.match(/(?:say|write|that)\s+(.+)/i);
                const message = messageMatch ? messageMatch[1] : '';
                
                openEmailModal(recipient, message);
                return;
            }
            
            // Rest of your existing sendMessage code...
            showTyping("Thinking...");
            
            try {
                const response = await window.pywebview.api.send_message(text);
                const data = JSON.parse(response);
                
                hideTyping();
                
                if (data.ok) {
                    addMessage(data.content, 'bot');
                    speak(data.content);
                } else {
                    addMessage(`Error: ${data.error || 'Unknown error'}`, 'bot');
                    speak("Sorry, there was an error.");
                }
            } catch (error) {
                hideTyping();
                addMessage(`System error: ${error}`, 'bot');
                speak("Sorry, there was a system error.");
            }
        }

        function hideWelcomeMessage() {
            const welcome = document.getElementById('welcome-message');
            if (welcome) {
                welcome.style.animation = 'fadeOut 0.5s ease forwards';
                setTimeout(() => {
                    welcome.remove();
                }, 500);
            }
        }
        
        function toggleVision() {
            isVisionActive = visionToggle.checked;
            
            if (isVisionActive) {
                statusDot.classList.add('vision-active');
                statusText.textContent = 'Vision Active';
                startVision();
            } else {
                statusDot.classList.remove('vision-active');
                statusText.textContent = 'Ready';
                stopVision();
            }
            
            // Save vision state
            saveSettings();
        }
        
        function startVision() {
            if (visionTimer) {
                clearInterval(visionTimer);
            }
            
            // Run immediately once
            analyzeScreen();
            
            // Then set interval
            visionTimer = setInterval(analyzeScreen, visionInterval * 1000);
        }
        
        function stopVision() {
            if (visionTimer) {
                clearInterval(visionTimer);
                visionTimer = null;
            }
            visionPreview.classList.remove('active');
        }
        
        async function analyzeScreen() {
            try {
                showTyping("Analyzing screen...");
                
                const result = await window.pywebview.api.analyze_screen();
                const data = JSON.parse(result);
                
                hideTyping();
                
                if (data.ok) {
                    addMessage(data.description, 'bot', 'vision');
                    
                    if (data.image_data) {
                        visionPreviewImg.src = `data:image/png;base64,${data.image_data}`;
                        visionPreview.classList.add('active');
                        
                        setTimeout(() => {
                            visionPreview.classList.remove('active');
                        }, 5000);
                    }
                } else {
                    addMessage(`Vision Error: ${data.error || 'Unknown error'}`, 'bot');
                }
            } catch (error) {
                hideTyping();
                addMessage(`Vision System Error: ${error}`, 'bot');
            } finally {
                statusText.textContent = isVisionActive ? 'Vision Active' : 'Ready';
            }
        }
        
        function openSettings() {
            settingsModal.classList.add('active');
            overlay.classList.add('active');
        }
        
        function closeSettings() {
            settingsModal.classList.remove('active');
            overlay.classList.remove('active');
        }
        
        function saveSettings() {
            // Here you would save settings to localStorage or backend
            closeSettings();
        }
        
        function openVisionSettings() {
            visionSettingsModal.classList.add('active');
            overlay.classList.add('active');
        }
        
        function closeVisionSettings() {
            visionSettingsModal.classList.remove('active');
            overlay.classList.remove('active');
        }
        
        function saveVisionSettings() {
            visionInterval = parseInt(visionIntervalInput.value) || 15;
            
            if (isVisionActive) {
                startVision(); // Restart with new interval
            }
            
            closeVisionSettings();
        }

        function openEmailModal(recipient = '', message = '') {
            emailRecipient.value = recipient;
            emailMessage.value = message;
            emailSubject.value = '';
            emailAttachments.value = '';
            emailCC.value = '';
            emailStatus.textContent = '';
            emailStatus.className = 'email-status';
            
            emailModal.classList.add('active');
            overlay.classList.add('active');
        }

        function closeEmailModal() {
            emailModal.classList.remove('active');
            overlay.classList.remove('active');
        }

        async function sendEmail() {
            const recipient = emailRecipient.value.trim();
            const subject = emailSubject.value.trim();
            const message = emailMessage.value.trim();
            const attachments = emailAttachments.value.trim();
            const cc = emailCC.value.trim();
            
            if (!recipient) {
                emailStatus.textContent = 'Recipient is required';
                emailStatus.className = 'email-status error';
                return;
            }
            
            emailStatus.textContent = 'Sending email...';
            emailStatus.className = 'email-status';
            
            try {
                const result = await window.pywebview.api.send_email(
                    recipient,
                    subject,
                    message,
                    attachments || 'no' , 
                    cc
                );
                
                if (result.includes('✅')) {
                    emailStatus.textContent = result;
                    emailStatus.className = 'email-status success';
                    setTimeout(closeEmailModal, 2000);
                } else {
                    emailStatus.textContent = result;
                    emailStatus.className = 'email-status error';
                }
            } catch (error) {
                emailStatus.textContent = `Error: ${error}`;
                emailStatus.className = 'email-status error';
            }
        }
        
        function loadSettings() {
            // Here you would load settings from localStorage or backend
            // For now we'll just set defaults
            visionIntervalInput.value = visionInterval;
            visionBlurToggle.checked = false;
        }
        
        // Initialize
        window.addEventListener('load', init);
    </script>
</body>
</html>
"""

class Api:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.vision_active = False
        self.vision_interval = VISION_INTERVAL
        self.blur_sensitive_region = BLUR_SENSITIVE_REGION
        self.sensitive_box = SENSITIVE_BOX

        # Add these lines to convert your images
        self.f1_base64 = self.image_to_base64(r"images/f1.jpg")  # Update path as needed
        self.f2_base64 = self.image_to_base64(r"images/f2.jpg")
        self.f3_base64 = self.image_to_base64(r"images/f3.jpg")
    
    def image_to_base64(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return ""

    def send_message(self, message):
        try:
            result = handle_intent(message.strip())
            return json.dumps({
                "ok": True,
                "content": result
            })
        except Exception as e:
            return json.dumps({
                "ok": False,
                "error": str(e)
            })

    def send_email(self, recipient, subject, message, attachments, cc):
        try:
            # Handle attachments
            attachment_list = []
            if attachments and attachments.lower() != 'no':
                for path in attachments.split(','):
                    path = path.strip()
                    if path:
                        expanded = os.path.expanduser(path)
                        if os.path.exists(expanded):
                            attachment_list.append(expanded)
                        else:
                            return f"Attachment not found: {path}"
            
            # Handle CC
            cc_list = [e.strip() for e in cc.split(',')] if cc else []
            
            # Build full message with subject
            full_message = f"Subject: {subject}\n\n{message}" if subject else message
            
            # Send using existing function
            result = send_email_with_attachments(recipient, cc_list, subject, full_message, attachment_list)
            return result
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    def minimize_window(self):
        webview.windows[0].minimize()
    
    def maximize_window(self):
        webview.windows[0].maximize()
    
    def restore_window(self):
        webview.windows[0].restore()
    
    def close_window(self):
        webview.windows[0].destroy()
        sys.exit()
    
    def start_listening(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {str(e)}"

    def speak(self, text: str):
        try:
            tts = gTTS(text=text, lang='en')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_path = fp.name
            tts.save(temp_path)
            
            # Use Linux-compatible audio player
            try:
                subprocess.run(["mpg123", temp_path], check=True)
            except FileNotFoundError:
                try:
                    subprocess.run(["mpv", temp_path], check=True)
                except FileNotFoundError:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_path], check=True)
            
            os.remove(temp_path)
        except Exception as e:
            print(f"TTS Error: {e}")

    def analyze_screen(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = VISION_SCREENSHOT_DIR / f"screenshot_{timestamp}.png"
            
            # Take screenshot
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # full virtual screen
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                img.save(filename)
            
            # Blur sensitive region if enabled
            if self.blur_sensitive_region:
                img = Image.open(filename)
                img = self.blur_vision_region(img, box=self.sensitive_box)
                img.save(filename)
            
            # Encode image
            b64_image = self.encode_image_base64(filename)
            
            # Send to OpenRouter
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe everything visible in this screenshot in detail. Mention objects, text, windows, and any notable activity."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                            }
                        ],
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {VISION_API_KEY}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(VISION_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            response_json = response.json()
            
            description = self.extract_description_from_response(response_json)
            
            # Delete screenshot if configured
            if DELETE_SCREENSHOT_AFTER_SEND and filename.exists():
                filename.unlink()
            
            return json.dumps({
                "ok": True,
                "description": description,
                "image_data": b64_image if not DELETE_SCREENSHOT_AFTER_SEND else None
            })
            
        except Exception as e:
            return json.dumps({
                "ok": False,
                "error": str(e)
            })

    def blur_vision_region(self, img: Image.Image, box=None, radius=20) -> Image.Image:
        """
        Blur a rectangular region to obscure sensitive data.
        box = (left, top, right, bottom). If None, blur center 30% area.
        """
        if box is None:
            w, h = img.size
            bw, bh = int(w * 0.3), int(h * 0.2)
            left = (w - bw) // 2
            top = (h - bh) // 2
            box = (left, top, left + bw, top + bh)

        # Crop the region, blur it, and paste back
        region = img.crop(box)
        blurred = region.filter(ImageFilter.GaussianBlur(radius))
        img.paste(blurred, box)
        return img

    def encode_image_base64(self, path: Path) -> str:
        with open(path, "rb") as f:
            raw = f.read()
        return base64.b64encode(raw).decode("utf-8")

    def extract_description_from_response(self, resp_json: dict) -> str:
        """
        OpenRouter's structure can vary slightly. This tries common places:
        - resp_json["choices"][0]["message"]["content"] could be a string or list/dict.
        We will fallback to dumping the full 'choices' for debugging.
        """
        try:
            choices = resp_json.get("choices", [])
            if not choices:
                return json.dumps(resp_json, indent=2)
            msg = choices[0].get("message", {})
            content = msg.get("content")
            # If content is a string, return it
            if isinstance(content, str):
                return content
            # If content is a list (blocks), try to extract text blocks
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        texts.append(block["text"])
                    elif isinstance(block, str):
                        texts.append(block)
                if texts:
                    return "\n".join(texts)
            # Else fallback to raw field "message"->"content" or the whole choices
            return json.dumps(msg, indent=2)
        except Exception as e:
            return f"Failed to parse response: {e}\nFull response: {json.dumps(resp_json)[:2000]}"

def start_ui():
    api = Api()
    window = webview.create_window(
        "👑 Lucifer AI - Premium Assistant",
        html=HTML,
        width=1000,
        height=700,
        min_size=(800, 600),
        text_select=True,
        js_api=api,
        frameless=True
    )
    webview.start(debug=True)

if __name__ == "__main__":
    # Check for required Linux packages
    try:
        subprocess.run(["which", "mpg123"], check=True)
    except subprocess.CalledProcessError:
        try:
            subprocess.run(["which", "mpv"], check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["which", "ffplay"], check=True)
            except subprocess.CalledProcessError:
                print("Warning: No compatible audio player found (mpg123, mpv, or ffplay). TTS will not work.")
    
    start_ui()
