# Voice2Text

A beautiful standalone voice-to-text app with OpenCode integration. Speak naturally into your microphone and get real-time transcription.

## Features

- Real-time speech-to-text transcription
- Continuous listening mode
- Word and character count
- Special character detection
- Copy transcribed text to clipboard
- Beautiful gradient UI
- Standalone desktop app (Electron)
- Flatpak packaging for easy Linux distribution
- OpenCode integration (copy text for AI prompts)

## Installation

### Option 1: Web App (Development)
```bash
git clone https://github.com/crhy/Voice2Text.git
cd Voice2Text
npm install
npm start
```
Open http://localhost:3000 in your browser.

### Option 2: Desktop App
```bash
git clone https://github.com/crhy/Voice2Text.git
cd Voice2Text
npm install
npm run build
npm run electron
```

### Option 3: Flatpak (Recommended for Linux)
Users can build their own Flatpak:
```bash
git clone https://github.com/crhy/Voice2Text.git
cd Voice2Text
npm install
npm run dist:linux
flatpak install Voice2Text.flatpak
flatpak run com.voice2text.app
```

## Usage

1. Launch the app
2. Click the microphone icon to start listening
3. Speak naturally - your words will appear as text in real-time
4. Click the copy icon to copy the transcribed text
5. Use the copied text as input for OpenCode or any other application

## Building from Source

### Prerequisites
- Node.js 16+
- npm
- For Flatpak: flatpak, flatpak-builder

### Build Commands
```bash
# Install dependencies
npm install

# Development
npm start              # Web app
npm run electron-dev   # Desktop app with hot reload

# Production
npm run build          # Build web app
npm run electron       # Run desktop app
npm run dist:linux     # Build Flatpak
```

## Integration with OpenCode

The app includes a "Copy to Clipboard" button for seamless integration with OpenCode. Simply:
1. Transcribe your speech
2. Click the copy button
3. Paste the text into OpenCode as your prompt

## Requirements

- Microphone access
- Modern browser with Web Speech API support (Chrome recommended)
- For desktop app: System with GUI support

## License

MIT
