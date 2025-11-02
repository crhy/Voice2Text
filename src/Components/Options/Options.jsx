import React, { useState } from "react";
import "./Options.css";

import ReactConfirmAlert, { confirmAlert } from "react-confirm-alert";
import "react-confirm-alert/src/react-confirm-alert.css";

import SpeechRecognition from "react-speech-recognition";

const Options = ({ setText, listening, text }) => {
  const [showDialog, setShowDialog] = useState(false);
  return (
    <>
      <div className="options-container">
        <div className="options">
          {(() => {
            if (!listening) {
              return (
                <i
                  title="Microphone"
                  className="fi fi-rr-microphone option"
                  onClick={SpeechRecognition.startListening}
                ></i>
              );
            } else {
              return (
                <i
                  className="fi fi-sr-microphone option"
                  onClick={SpeechRecognition.stopListening}
                ></i>
              );
            }
          })()}

          <i
            title="Clear Text"
            className="fi fi-rr-trash option"
            onClick={() => {
              if (text.length > 0) {
                setShowDialog(true);
              }
            }}
          ></i>
          {text.length > 0 && (
            <i
              title="Copy Text to Clipboard"
              className="fi fi-rr-copy option"
              onClick={() => navigator.clipboard.writeText(text)}
            ></i>
          )}
        </div>
      </div>

      <div>
        {text.length > 0 &&
          showDialog &&
          confirmAlert({
            customUI: ({ onClose }) => {
              return (
                <div className="modal-container">
                  <p className="mheading">Are you sure?</p>
                  <p className="mtagline">You want to delete this Text?</p>
                  <div className="mbtns">
                    <button className="mno" onClick={onClose}>
                      No
                    </button>
                    <button
                      className="myes"
                      onClick={() => {
                        setShowDialog(false);
                        setText("");
                        onClose();
                      }}
                    >
                      Yes, Delete it!
                    </button>
                  </div>
                </div>
              );
            },
          })}
      </div>
    </>
  );
};

export default Options;
