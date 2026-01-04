import { useState, useEffect, useRef } from 'react'
import './OllieAvatar.css'

function OllieAvatar({ isSpeaking, isThinking, isListening }) {
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [pulseScale, setPulseScale] = useState(1)
  const animationFrameRef = useRef(null)

  useEffect(() => {
    let animationId = null
    const startTime = performance.now()
    
    const animate = (currentTime) => {
      const elapsed = (currentTime - startTime) / 1000
      
      if (isSpeaking) {
        const radius = 30
        const speed = 0.5
        const angle = elapsed * speed
        const x = Math.cos(angle) * radius
        const y = Math.sin(angle) * radius
        
        setPosition({ x, y })
        const pulse = 1 + Math.sin(elapsed * 4) * 0.1
        setPulseScale(pulse)
        animationId = requestAnimationFrame(animate)
      } else if (isThinking) {
        const radius = 15
        const speed = 0.3
        const angle = elapsed * speed
        const x = Math.cos(angle) * radius
        const y = Math.sin(angle) * radius
        
        setPosition({ x, y })
        setPulseScale(1 + Math.sin(elapsed * 2) * 0.05)
        animationId = requestAnimationFrame(animate)
      } else {
        const floatY = Math.sin(elapsed * 0.5) * 10
        setPosition({ x: 0, y: floatY })
        setPulseScale(1)
        animationId = requestAnimationFrame(animate)
      }
    }
    
    animationId = requestAnimationFrame(animate)
    
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [isSpeaking, isThinking, isListening])

  const getStateClass = () => {
    if (isSpeaking) return 'speaking'
    if (isThinking) return 'thinking'
    if (isListening) return 'listening'
    return 'idle'
  }

  return (
    <>
      {/* Simple test to verify component renders */}
      <div style={{
        position: 'fixed',
        top: '100px',
        right: '100px',
        width: '200px',
        height: '200px',
        background: 'blue',
        borderRadius: '50%',
        zIndex: 9999
      }}>
        AVATAR TEST
      </div>
      <div 
        className={`ollie-avatar ${getStateClass()}`}
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${pulseScale})`,
          transition: isSpeaking ? 'none' : 'transform 0.3s ease-out'
        }}
      >
        <div className="avatar-core">
        <div className="avatar-glow"></div>
        <div className="avatar-surface">
          <div className="avatar-pattern"></div>
        </div>
        {isSpeaking && (
          <>
            <div className="sound-wave wave-1"></div>
            <div className="sound-wave wave-2"></div>
            <div className="sound-wave wave-3"></div>
          </>
        )}
        {isThinking && (
          <div className="thinking-indicator">
            <div className="thinking-dot"></div>
            <div className="thinking-dot"></div>
            <div className="thinking-dot"></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default OllieAvatar
