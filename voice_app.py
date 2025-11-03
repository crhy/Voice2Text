#!/usr/bin/env python3
"""
Voice-to-OpenCode GUI Application

A standalone GUI app for voice recognition that integrates with OpenCode.
Features a simple interface with start/stop buttons and automatic clipboard copying.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyperclip
import threading
import time
import os
import json
import pyaudio
import numpy as np
import tempfile
import wave
from faster_whisper import WhisperModel
from scipy.signal import resample
import torch
import requests
import pyttsx3
from gtts import gTTS
import pygame
import os
from PIL import Image, ImageTk
from pydub import AudioSegment

class VoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice To AI")
        self.root.geometry("900x800")
        self.root.configure(bg='#000033')  # Dark blue gradient approximation
        self.root.resizable(True, True)

        # Config
        self.config_file = 'voice_config.json'
        self.config = self.load_config()

        # Audio devices
        self.audio = pyaudio.PyAudio()
        self.microphones = self.get_microphones()
        self.selected_mic_index = self.config.get('microphone_index', 0)

        # Speech recognition with Faster Whisper
        print("Loading Whisper model... (this may take a minute on first run)")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Using device: {device}, compute_type: {compute_type}")
        self.model = WhisperModel("small", device=device, compute_type=compute_type)  # Small model optimized for GPU
        print("Model loaded!")

        # Text-to-speech with gTTS and pygame
        pygame.mixer.init()
        self.tts_playing = False

        # Ollama models
        self.ollama_models = self.get_ollama_models()
        self.selected_model = self.config.get('selected_model', "llama3.2" if "llama3.2" in self.ollama_models else (self.ollama_models[0] if self.ollama_models else "llama3.2"))
        self.is_listening = False
        self.current_text = ""
        self.audio_stream = None
        self.audio_frames = []

        # GUI elements
        self.create_gui()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_ollama_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json()['models']]
                return models
            else:
                return []
        except:
            return []

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        config = {
            'microphone_index': self.selected_mic_index,
            'selected_model': self.selected_model
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def on_close(self):
        self.save_config()
        self.audio.terminate()
        self.root.destroy()

    def get_microphones(self):
        microphones = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            max_input = info.get('maxInputChannels', 0)
            if isinstance(max_input, (int, float)) and max_input > 0:
                microphones.append(f"{info.get('name')} (Index: {i})")
        return microphones

    def get_mic_device_index(self, mic_string):
        import re
        match = re.search(r'Index: (\d+)', mic_string)
        return int(match.group(1)) if match else 0

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_listening:
            self.audio_frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def create_gui(self):
        # Style
        style = ttk.Style()
        style.configure('TFrame', background='#000033')
        style.configure('TButton', font=('Helvetica', 12), padding=10)
        style.configure('TLabel', font=('Helvetica', 10), background='#000033', foreground='white')
        style.configure('TCombobox', font=('Helvetica', 10), background='#000033', fieldbackground='#000022', foreground='white', selectbackground='#000055', selectforeground='white')

        # Title
        title_label = ttk.Label(self.root, text="Voice To AI", font=('Helvetica', 16, 'bold'), background='#000000')
        title_label.pack(pady=10)

        # Version
        version_label = ttk.Label(self.root, text="v0.01", font=('Helvetica', 8), background='#000000', foreground='white')
        version_label.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        # Microphone selection
        mic_frame = ttk.Frame(self.root)
        mic_frame.pack(pady=5, padx=20, fill='x')

        ttk.Label(mic_frame, text="Microphone:").pack(side='left')
        self.mic_var = tk.StringVar()
        self.mic_menu = tk.OptionMenu(mic_frame, self.mic_var, *self.microphones, command=self.on_mic_change)
        self.mic_menu.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.mic_menu.config(bg='#000033', fg='white', activebackground='#000055', activeforeground='white', highlightbackground='#000033', highlightcolor='#000033')
        if self.microphones:
            self.mic_var.set(self.microphones[self.selected_mic_index])

        # AI Model selection
        model_frame = ttk.Frame(self.root)
        model_frame.pack(pady=5, padx=20, fill='x')

        ttk.Label(model_frame, text="AI Model:").pack(side='left')
        self.model_var = tk.StringVar()
        self.model_menu = tk.OptionMenu(model_frame, self.model_var, *self.ollama_models if self.ollama_models else ["No models found"])
        self.model_menu.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.model_menu.config(bg='#000033', fg='white', activebackground='#000055', activeforeground='white', highlightbackground='#000033', highlightcolor='#000033')
        if self.ollama_models:
            self.model_var.set(self.selected_model)
        self.model_var.trace('w', self.on_model_change)

        # Status label
        self.status_label = ttk.Label(self.root, text="Ready", font=('Helvetica', 12))
        self.status_label.pack(pady=10)

        # Text area
        text_frame = ttk.Frame(self.root)
        text_frame.pack(pady=5, padx=20, fill='x')

        ttk.Label(text_frame, text="Transcribed Text:").pack(anchor='w')
        self.text_area = scrolledtext.ScrolledText(text_frame, height=15, wrap=tk.WORD,
                                                  bg='#000022', fg='white', insertbackground='white',
                                                  font=('Consolas', 10))
        self.text_area.pack(fill='x', expand=False)

        # AI Response area
        ai_frame = ttk.Frame(self.root)
        ai_frame.pack(pady=5, padx=20, fill='x')

        ttk.Label(ai_frame, text="AI Response:").pack(anchor='w')
        self.ai_text_area = scrolledtext.ScrolledText(ai_frame, height=12, wrap=tk.WORD,
                                                     bg='#000022', fg='white', insertbackground='white',
                                                     font=('Consolas', 10))
        self.ai_text_area.pack(fill='x', expand=False)

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=2)

        self.start_button = ttk.Button(button_frame, text="🎙️ Start Dictation",
                                      command=self.start_dictation)
        self.start_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Dictation",
                                     command=self.stop_dictation, state='disabled')
        self.stop_button.pack(side='left', padx=5)

        self.copy_button = ttk.Button(button_frame, text="📋 Copy",
                                      command=self.copy_text)
        self.copy_button.pack(side='left', padx=5)

        self.send_ai_button = ttk.Button(button_frame, text="🤖 Send to AI",
                                         command=self.send_to_ai)
        self.send_ai_button.pack(side='left', padx=5)

        self.stop_tts_button = ttk.Button(button_frame, text="⏹️ Stop TTS",
                                          command=self.stop_tts)
        self.stop_tts_button.pack(side='left', padx=5)

        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear",
                                       command=self.clear_text)
        self.clear_button.pack(side='left', padx=5)



    def on_mic_change(self, value):
        try:
            self.selected_mic_index = self.microphones.index(value)
            self.save_config()
            self.update_status(f"Selected: {value.split(' (')[0]}")
        except ValueError:
            pass

    def on_model_change(self, *args):
        self.selected_model = self.model_var.get()
        self.update_status(f"AI Model: {self.selected_model}")

    def update_status(self, message, color='black'):
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def start_dictation(self):
        if not self.microphones:
            messagebox.showerror("Error", "No microphones found!")
            return

        self.is_listening = True
        self.current_text = ""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "🎙️ Listening... Speak now!\n\n")

        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.update_status("🎙️ Listening...", "#00aa00")

        # Start listening in background thread
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def stop_dictation(self):
        self.is_listening = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

        if self.current_text.strip():
            pyperclip.copy(self.current_text.strip())
            self.update_status("📋 Text copied to clipboard!", "#0066cc")
            # Send to Ollama and speak response
            threading.Thread(target=self.query_ollama_and_speak, args=(self.current_text.strip(),), daemon=True).start()
        else:
            self.update_status("Ready", "black")

        # Small delay to ensure audio stream is fully closed
        time.sleep(0.1)

    def copy_text(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.update_status("📋 Text copied to clipboard!", "#0066cc")
        else:
            self.update_status("No text to copy", "black")

    def send_to_ai(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            self.update_status("🤖 Sending to AI...", "#ffaa00")
            threading.Thread(target=self.query_ollama_and_speak, args=(text,), daemon=True).start()
        else:
            self.update_status("No text to send to AI", "black")

    def query_ollama_and_speak(self, user_text):
        try:
            # Check if Ollama is running
            if not self.ollama_models:
                self.update_status("Ollama not running - start with 'ollama serve'", "red")
                return

            self.update_status("🤖 Querying AI...", "#ffaa00")
            # Query Ollama
            response = requests.post('http://localhost:11434/api/generate',
                                   json={
                                       "model": self.selected_model,
                                       "prompt": user_text,
                                       "stream": False
                                   },
                                   timeout=60)
            if response.status_code == 200:
                ai_response = response.json()['response'].strip()
                if ai_response:
                    # Display AI response
                    self.ai_text_area.delete(1.0, tk.END)
                    self.ai_text_area.insert(tk.END, ai_response)
                    # Speak the response with gTTS
                    self.speak_with_gtts(ai_response)
                    self.update_status("🤖 AI responded!", "#00aa00")
                else:
                    self.update_status("AI gave empty response", "orange")
            else:
                self.update_status(f"Ollama error: {response.status_code}", "red")
        except requests.exceptions.Timeout:
            self.update_status("AI timeout - model may be slow", "red")
        except requests.exceptions.ConnectionError:
            self.update_status("Cannot connect to Ollama - check if running", "red")
        except Exception as e:
            self.update_status(f"AI error: {str(e)[:50]}", "red")

    def speak_with_gtts(self, text):
        try:
            self.tts_playing = True
            tts = gTTS(text=text, lang='en', slow=False)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            # Speed up audio
            audio = AudioSegment.from_mp3(temp_file.name)
            faster_audio = audio.speedup(playback_speed=1.3)  # 30% faster
            sped_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            faster_audio.export(sped_file.name, format='mp3')
            pygame.mixer.music.load(sped_file.name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and self.tts_playing:
                pygame.time.wait(100)
            pygame.mixer.music.stop()
            os.unlink(temp_file.name)
            os.unlink(sped_file.name)
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            self.tts_playing = False

    def stop_tts(self):
        self.tts_playing = False
        pygame.mixer.music.stop()
        self.update_status("TTS stopped", "orange")

    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.ai_text_area.delete(1.0, tk.END)
        self.current_text = ""
        self.update_status("Ready", "black")

    def listen_loop(self):
        try:
            device_index = self.get_mic_device_index(self.microphones[self.selected_mic_index])

            # Start audio stream - try different sample rates
            self.audio_frames = []
            sample_rates = [48000, 44100, 32000, 22050, 16000, 8000]  # Try common rates

            for rate in sample_rates:
                try:
                    self.audio_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024,
                        stream_callback=self.audio_callback
                    )
                    self.sample_rate = rate
                    break
                except Exception as e:
                    print(f"Failed to open stream at {rate} Hz: {e}")
                    continue
            else:
                raise Exception("Could not open audio stream at any supported sample rate")

            self.audio_stream.start_stream()
            self.root.after(0, lambda: self.update_status("🎙️ Listening... (real-time)", "#00aa00"))

            processed_frames = 0
            chunk_duration = 2  # seconds for faster real-time display with good accuracy

            # Real-time transcription loop
            while self.is_listening:
                time.sleep(chunk_duration)

                # Check if we have new frames to process
                if len(self.audio_frames) > processed_frames:
                    chunk_frames = self.audio_frames[processed_frames:]
                    processed_frames = len(self.audio_frames)

                    # Process this chunk
                    self.root.after(0, lambda: self.update_status("🔍 Recognizing...", "#ffaa00"))
                    try:
                        # Convert chunk to numpy and resample
                        audio_data = np.frombuffer(b''.join(chunk_frames), dtype=np.int16)
                        if self.sample_rate != 16000:
                            num_samples = len(audio_data)
                            target_samples = int(num_samples * 16000 / self.sample_rate)
                            audio_data = resample(audio_data, target_samples).astype(np.int16)

                        # Save chunk to temp WAV
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                            temp_filename = temp_file.name

                            with wave.open(temp_filename, 'wb') as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(16000)
                                wf.writeframes(audio_data.tobytes())

                        # Transcribe chunk
                        segments, info = self.model.transcribe(temp_filename, language="en")
                        text = " ".join(segment.text for segment in segments).strip()

                        os.unlink(temp_filename)

                        if text:
                            self.current_text += text + " "
                            self.root.after(0, self.update_transcript, text)
                            self.root.after(0, lambda: self.update_status("🎙️ Listening... (real-time)", "#00aa00"))
                        else:
                            self.root.after(0, lambda: self.update_status("🎙️ Listening... (real-time)", "#00aa00"))

                    except Exception as e:
                        self.root.after(0, self.update_transcript, f"[Error: {e}]")
                        self.root.after(0, lambda: self.update_status("🎙️ Listening... (real-time)", "#00aa00"))

            # Stop recording
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

            # Process any remaining frames
            if len(self.audio_frames) > processed_frames:
                remaining_frames = self.audio_frames[processed_frames:]
                self.root.after(0, lambda: self.update_status("🔍 Finalizing...", "#ffaa00"))
                try:
                    audio_data = np.frombuffer(b''.join(remaining_frames), dtype=np.int16)
                    if self.sample_rate != 16000:
                        num_samples = len(audio_data)
                        target_samples = int(num_samples * 16000 / self.sample_rate)
                        audio_data = resample(audio_data, target_samples).astype(np.int16)

                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_filename = temp_file.name

                        with wave.open(temp_filename, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(16000)
                            wf.writeframes(audio_data.tobytes())

                    segments, info = self.model.transcribe(temp_filename, language="en")
                    text = " ".join(segment.text for segment in segments).strip()

                    os.unlink(temp_filename)

                    if text:
                        self.current_text += text + " "
                        self.root.after(0, self.update_transcript, text)

                except Exception as e:
                    self.root.after(0, self.update_transcript, f"[Error: {e}]")

            self.root.after(0, lambda: self.update_status("Ready", "black"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Recognition error: {e}"))
            self.root.after(0, self.stop_dictation)

    def update_transcript(self, text):
        self.text_area.insert(tk.END, f"{text}\n")
        self.text_area.see(tk.END)
        self.root.update_idletasks()

def main():
    try:
        root = tk.Tk()
        app = VoiceApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install required packages:")
        print("pip install SpeechRecognition pyperclip pyaudio pocketsphinx")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()