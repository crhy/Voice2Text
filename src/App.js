import "./App.css";
import Navbar from "./Components/Navbar/Navbar.jsx";
import Editor from "./Components/Editor/Editor.jsx";
import Options from "./Components/Options/Options.jsx";
import Details from "./Components/Details/Details";

import { useEffect, useState } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";

import { createSpeechlySpeechRecognition } from "@speechly/speech-recognition-polyfill";

const appId = 'a1e6781b-494b-4a88-adfc-599724a002f0';
const SpeechlySpeechRecognition = createSpeechlySpeechRecognition(appId);
SpeechRecognition.applyPolyfill(SpeechlySpeechRecognition);

function App() {
  const [text, setText] = useState("");
  const [words, setWords] = useState(0);
  const [characters, setCharacters] = useState(0);
  const [special, setSpecial] = useState(0);
  const [microphones, setMicrophones] = useState([]);
  const [selectedMic, setSelectedMic] = useState('');
  const [micPermission, setMicPermission] = useState('unknown'); // 'unknown', 'granted', 'denied'
  let format = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;
  let localcount = 0;

  const { transcript, listening, browserSupportsSpeechRecognition } =
    useSpeechRecognition();
  const startListening = () =>
    SpeechRecognition.startListening({
      continuous: true,
      language: 'en-US'
    });

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
    if (transcript.length > 0 && text.length > 0) {
      setText(text + " " + transcript.toLowerCase());
    } else if (transcript.length > 0) {
      setText(transcript.toLowerCase());
    }
  }, [listening]);

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


      <Options setText={setText} listening={listening} text={text} />
    </div>
  );
}

export default App;
