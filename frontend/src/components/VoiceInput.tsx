/**
 * VoiceInput — microphone button that uses the Web Speech API to
 * transcribe spoken answers into text.
 *
 * How it works:
 * - Uses webkitSpeechRecognition (Chrome/Edge) or SpeechRecognition (standard)
 * - Continuous mode: keeps listening until the user stops it
 * - Interim results shown in real-time (light text), then finalized
 * - Appends transcribed text to the existing textarea content
 * - Falls back gracefully: shows a tooltip if the browser doesn't support it
 *
 * Browser support:
 * - Chrome/Edge: Full support (uses Google's speech recognition service)
 * - Safari: Partial (requires user gesture, may not support continuous)
 * - Firefox: Not supported (component hides itself)
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Tooltip,
  Typography,
} from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";
import MicOffIcon from "@mui/icons-material/MicOff";

// TypeScript doesn't include Web Speech API types by default
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: Event & { error: string }) => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

// ---------------------------------------------------------------------------
// Check browser support
// ---------------------------------------------------------------------------

function getSpeechRecognition(): (new () => SpeechRecognition) | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface VoiceInputProps {
  /** Called with transcribed text to append to the answer */
  onTranscript: (text: string) => void;
  /** Whether the parent input is disabled */
  disabled?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check support on mount
  useEffect(() => {
    setSupported(!!getSpeechRecognition());
  }, []);

  const startListening = useCallback(() => {
    const SpeechRecognitionClass = getSpeechRecognition();
    if (!SpeechRecognitionClass) return;

    const recognition = new SpeechRecognitionClass();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalTranscript) {
        onTranscript(finalTranscript);
        setInterimText("");
      } else {
        setInterimText(interim);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimText("");
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      setIsListening(false);
      setInterimText("");
    };

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [onTranscript]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  // Don't render if browser doesn't support speech recognition
  if (!supported) return null;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Tooltip
        title={
          isListening
            ? "Click to stop recording"
            : "Click to dictate your answer"
        }
      >
        <span>
          <Button
            variant={isListening ? "contained" : "outlined"}
            color={isListening ? "error" : "primary"}
            startIcon={isListening ? <MicOffIcon /> : <MicIcon />}
            onClick={isListening ? stopListening : startListening}
            disabled={disabled}
            size="small"
            sx={
              isListening
                ? {
                    animation: "pulse 1.5s infinite",
                    "@keyframes pulse": {
                      "0%": { boxShadow: "0 0 0 0 rgba(244,67,54,0.4)" },
                      "70%": { boxShadow: "0 0 0 10px rgba(244,67,54,0)" },
                      "100%": { boxShadow: "0 0 0 0 rgba(244,67,54,0)" },
                    },
                  }
                : {}
            }
          >
            {isListening ? "Stop" : "Dictate"}
          </Button>
        </span>
      </Tooltip>

      {isListening && (
        <Chip
          label="Listening..."
          color="error"
          size="small"
          variant="outlined"
          sx={{ animation: "pulse 1.5s infinite" }}
        />
      )}

      {interimText && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            fontStyle: "italic",
            maxWidth: 300,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {interimText}
        </Typography>
      )}
    </Box>
  );
}
