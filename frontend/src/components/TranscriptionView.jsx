import './TranscriptionView.css'

function TranscriptionView({ transcript, isRecording, onStart, onStop, onClear, ollieResponse }) {
  return (
    <div className="transcription-view">
      <div className="controls">
        <button
          className={`record-button ${isRecording ? 'recording' : ''}`}
          onClick={isRecording ? onStop : onStart}
        >
          {isRecording ? (
            <>
              <span className="recording-indicator"></span>
              Stop Recording
            </>
          ) : (
            <>
              <span className="mic-icon">🎤</span>
              Start Recording
            </>
          )}
        </button>
        
        {transcript && (
          <button className="clear-button" onClick={onClear}>
            Clear
          </button>
        )}
      </div>
      
      <div className="transcript-container">
        <div className="transcript-header">
          <h2>Live Transcription</h2>
          {isRecording && (
            <span className="live-badge">LIVE</span>
          )}
        </div>
        
        <div className="transcript-content">
          {transcript ? (
            <div className="transcript-section">
              <p className="transcript-label">You:</p>
              <p className="transcript-text">{transcript}</p>
            </div>
          ) : (
            <p className="transcript-placeholder">
              {isRecording 
                ? 'Listening... Speak into your microphone.' 
                : 'Click "Start Recording" to begin real-time transcription.'}
            </p>
          )}
          
          {ollieResponse && (
            <div className="transcript-section ollie-response">
              <p className="transcript-label">Ollie:</p>
              <p className="transcript-text ollie-text">{ollieResponse}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TranscriptionView

