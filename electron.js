const { app, BrowserWindow, systemPreferences } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

// Enable speech recognition in Electron
app.commandLine.appendSwitch('--enable-speech-dispatcher');
app.commandLine.appendSwitch('--enable-experimental-web-platform-features');
app.commandLine.appendSwitch('--enable-features', 'WebSpeechAPI');
app.commandLine.appendSwitch('--disable-web-security');
app.commandLine.appendSwitch('--allow-running-insecure-content');

async function requestMicrophoneAccess() {
  try {
    if (process.platform === 'darwin') {
      const result = await systemPreferences.askForMediaAccess('microphone');
      return result;
    } else {
      // For Windows/Linux, permissions are handled by the browser
      return true;
    }
  } catch (error) {
    console.error('Error requesting microphone access:', error);
    return false;
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: false, // Allow speech recognition API
      allowRunningInsecureContent: true, // Allow mixed content for speech API
      sandbox: false, // Disable sandboxing for speech recognition
      experimentalFeatures: true, // Enable experimental features
    },
    icon: path.join(__dirname, 'public/favicon.ico'), // Add icon if available
  });

  // Set user agent to mimic Chrome browser
  mainWindow.webContents.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build/index.html'));
  }

  // Request microphone permissions
  requestMicrophoneAccess().then((granted) => {
    if (granted) {
      console.log('Microphone access granted');
    } else {
      console.log('Microphone access denied');
    }
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});