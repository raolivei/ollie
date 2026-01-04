import { useState, useRef, useEffect } from 'react'
import TranscriptionView from './components/TranscriptionView'
import OllieAvatar from './components/OllieAvatar'
import './App.css'

// Use relative URLs when in browser, or environment variables
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  // In browser, use relative path (nginx will proxy to core:8000)
  if (typeof window !== 'undefined') return '/api'
  return 'http://localhost:8000'
}

const getWsUrl = () => {
  if (import.meta.env.VITE_WHISPER_WS_URL) return import.meta.env.VITE_WHISPER_WS_URL
  // In browser, use relative WebSocket URL (nginx will proxy to whisper:8000)
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws/transcribe`
  }
  return 'ws://localhost:8000/ws/transcribe'
}

const API_URL = getApiUrl()
const WHISPER_WS_URL = getWsUrl()

function App() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [ollieResponse, setOllieResponse] = useState('')
  const [isOllieSpeaking, setIsOllieSpeaking] = useState(false)
  const [isOllieThinking, setIsOllieThinking] = useState(false)
  
  const mediaRecorderRef = useRef(null)
  const websocketRef = useRef(null)
  const sessionIdRef = useRef(null)
  const audioContextRef = useRef(null)
  const streamRef = useRef(null)
  const audioRef = useRef(null)

  useEffect(() => {
    // Generate session ID on mount
    sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    return () => {
      // Cleanup on unmount
      if (websocketRef.current) {
        websocketRef.current.close()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      setError(null)
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })
      
      streamRef.current = stream
      
      // Create AudioContext for processing
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      })
      audioContextRef.current = audioContext
      
      const source = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      
      // Connect WebSocket
      const ws = new WebSocket(WHISPER_WS_URL)
      websocketRef.current = ws
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'transcription_update') {
            // Append new text to transcript
            setTranscript(prev => {
              // If it's a continuation, just append the new part
              if (data.full_text && prev && data.full_text.startsWith(prev)) {
                return data.full_text
              }
              // Otherwise, append with space
              return prev ? `${prev} ${data.text}` : data.text
            })
          } else if (data.type === 'transcription_final') {
            setTranscript(data.text)
          } else if (data.type === 'error') {
            setError(data.message)
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection error')
        setIsConnected(false)
      }
      
      ws.onclose = () => {
        setIsConnected(false)
      }
      
      // Process audio chunks
      let wsReady = false
      ws.onopen = () => {
        setIsConnected(true)
        wsReady = true
        // Send session ID first
        ws.send(sessionIdRef.current)
      }
      
      let chunkCount = 0
      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN && wsReady) {
          const inputData = e.inputBuffer.getChannelData(0)
          
          // Check if we have actual audio data (not silence)
          const hasAudio = inputData.some(sample => Math.abs(sample) > 0.01)
          
          if (hasAudio) {
            // Convert Float32Array to Int16Array (PCM 16-bit)
            const int16Data = new Int16Array(inputData.length)
            for (let i = 0; i < inputData.length; i++) {
              // Clamp and convert to 16-bit integer
              const s = Math.max(-1, Math.min(1, inputData[i]))
              int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
            }
            
            // Send audio chunk via WebSocket
            try {
              ws.send(int16Data.buffer)
              chunkCount++
              if (chunkCount % 100 === 0) {
                console.log(`Sent ${chunkCount} audio chunks`)
              }
            } catch (err) {
              console.error('Error sending audio chunk:', err)
            }
          }
        }
      }
      
      source.connect(processor)
      processor.connect(audioContext.destination)
      
      setIsRecording(true)
      
    } catch (err) {
      console.error('Error starting recording:', err)
      setError(`Failed to start recording: ${err.message}`)
    }
  }

  const sendToChat = async (message) => {
    if (!message || !message.trim()) return
    
    setIsOllieThinking(true)
    setIsOllieSpeaking(false)
    
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: null
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setOllieResponse(data.response)
        setIsOllieThinking(false)
        setIsOllieSpeaking(true)
        
        // If there's an audio URL, play it
        if (data.audio_url) {
          if (audioRef.current) {
            audioRef.current.pause()
            audioRef.current.src = data.audio_url
            audioRef.current.play()
            
            audioRef.current.onended = () => {
              setIsOllieSpeaking(false)
            }
          }
        } else {
          // Simulate speaking duration based on response length
          const speakingDuration = Math.min(data.response.length * 50, 5000)
          setTimeout(() => {
            setIsOllieSpeaking(false)
          }, speakingDuration)
        }
      } else {
        setIsOllieThinking(false)
        setError('Failed to get response from Ollie')
      }
    } catch (err) {
      console.error('Error sending to chat:', err)
      setIsOllieThinking(false)
      setError(`Chat error: ${err.message}`)
    }
  }

  const stopRecording = async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    
    // Save transcription if we have one
    if (transcript && transcript.trim()) {
      try {
        const response = await fetch(`${API_URL}/save_streaming_transcription`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            transcript: transcript,
            session_id: null // Let backend create new session
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          console.log('Transcription saved:', data)
          
          // Automatically send to chat for Ollie's response
          sendToChat(transcript)
        }
      } catch (err) {
        console.error('Error saving transcription:', err)
      }
    }
    
    if (websocketRef.current) {
      websocketRef.current.close()
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
    
    setIsRecording(false)
    setIsConnected(false)
  }

  const clearTranscript = () => {
    setTranscript('')
  }

  return (
    <div className="app">
      <div className="avatar-container">
        {/* Test element to verify container renders */}
        <div style={{ 
          position: 'fixed', 
          top: '20px', 
          right: '20px', 
          width: '100px', 
          height: '100px', 
          background: 'red', 
          zIndex: 9999,
          display: 'block'
        }}>
          TEST
        </div>
        <OllieAvatar 
          isSpeaking={isOllieSpeaking}
          isThinking={isOllieThinking}
          isListening={isRecording}
        />
      </div>
      
      <div className="container">
        <header className="header">
          <h1>Ollie</h1>
          <p className="subtitle">Real-time Transcription with Rolling Window</p>
        </header>
        
        <div className="status-bar">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}
        </div>
        
        <TranscriptionView 
          transcript={transcript}
          isRecording={isRecording}
          onStart={startRecording}
          onStop={stopRecording}
          onClear={clearTranscript}
          ollieResponse={ollieResponse}
        />
      </div>
      
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  )
}

export default App

