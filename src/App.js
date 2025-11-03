import "./App.css";
import Navbar from "./Components/Navbar/Navbar.jsx";
import Editor from "./Components/Editor/Editor.jsx";
import Options from "./Components/Options/Options.jsx";
import Details from "./Components/Details/Details";

import { useEffect, useState, useRef } from "react";

function App() {
  const [text, setText] = useState("");
  const [words, setWords] = useState(0);
  const [characters, setCharacters] = useState(0);
  const [special, setSpecial] = useState(0);
  const [microphones, setMicrophones] = useState([]);
  const [selectedMic, setSelectedMic] = useState('');
  const [micPermission, setMicPermission] = useState('unknown'); // 'unknown', 'granted', 'denied'
  const [listening, setListening] = useState(false);
  const [browserSupportsSpeechRecognition, setBrowserSupportsSpeechRecognition] = useState(false);
  const recognitionRef = useRef(null);
  let format = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;
  let localcount = 0;

  useEffect(() => {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    console.log('SpeechRecognition available:', !!SpeechRecognition);
    if (SpeechRecognition) {
      setBrowserSupportsSpeechRecognition(true);
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';
      console.log('Speech recognition initialized:', recognitionRef.current);

      recognitionRef.current.onresult = (event) => {
        console.log('Speech recognition result:', event);
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        console.log('Final transcript:', finalTranscript);
        if (finalTranscript) {
          setText(prevText => prevText + (prevText ? ' ' : '') + finalTranscript.toLowerCase());
        }
      };

      recognitionRef.current.onstart = () => {
        console.log('Speech recognition started');
        setListening(true);
      };

      recognitionRef.current.onend = () => {
        console.log('Speech recognition ended');
        setListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error, event);
        setListening(false);
      };
    }
  }, []);

  const startListening = () => {
    console.log('Starting speech recognition...');
    if (recognitionRef.current && !listening) {
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && listening) {
      recognitionRef.current.stop();
    }
  };

  useEffect(() => {
    if (text) {
      setCharacters(text.length);
      setWords(text.split(" ").length);

      for (let index = 0; index < text.length; index++) {
        if (format.test(text.charAt(index))) {
          localcount += 1;
        }
      }
      setSpecial(localcount);
    } else {
      setCharacters(0);
      setWords(0);
      setSpecial(0);
    }
  }, [text]);



  useEffect(() => {
    // Check microphone permissions
    navigator.permissions.query({ name: 'microphone' })
      .then(result => {
        setMicPermission(result.state);
        result.onchange = () => setMicPermission(result.state);
      })
      .catch(() => {
        // Fallback for browsers that don't support permissions API
        setMicPermission('unknown');
      });

    // Get available microphones
    navigator.mediaDevices.enumerateDevices()
      .then(devices => {
        const mics = devices.filter(device => device.kind === 'audioinput');
        setMicrophones(mics);
        if (mics.length > 0 && !selectedMic) {
          setSelectedMic(mics[0].deviceId);
        }
      })
      .catch(err => console.error('Error getting microphones:', err));
  }, [selectedMic]);



  if (!browserSupportsSpeechRecognition) {
    return (
      <div className="App">
        <Navbar />
        <div className="main-container">
          <div className="error-message">
            <h2>⚠️ Speech Recognition Not Supported</h2>
            <p>Your browser doesn't support speech recognition.</p>
            <p>Please use a modern browser like Chrome or Edge.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <Navbar />
      <div className="status-bar">
        <div className={`mic-status ${micPermission}`}>
          <span className="status-icon">
            {micPermission === 'granted' ? '🎤' : micPermission === 'denied' ? '🚫' : '❓'}
          </span>
          <span className="status-text">
            {micPermission === 'granted' ? 'Microphone Ready' :
             micPermission === 'denied' ? 'Microphone Access Denied' :
             'Click microphone to grant access'}
          </span>
        </div>
        {microphones.length > 1 && (
          <select
            value={selectedMic}
            onChange={(e) => setSelectedMic(e.target.value)}
            className="mic-dropdown"
          >
            {microphones.map((mic) => (
              <option key={mic.deviceId} value={mic.deviceId}>
                {mic.label || `Microphone ${mic.deviceId.slice(0, 8)}`}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="main-container">
         <Editor text={text} setText={setText} />
        <Details
          words={words}
          characters={characters}
          special={special}
          listening={listening}
          browserSupportsSpeechRecognition={browserSupportsSpeechRecognition}
        />
      </div>


      <Options setText={setText} listening={listening} text={text} startListening={startListening} stopListening={stopListening} />
    </div>
  );
}

export default App;
