import { useRef, useCallback } from 'react'
import Webcam from 'react-webcam'

/**
 * WebcamCapture — wraps react-webcam.
 * Props:
 *   onCapture(blob): called when the user clicks Capture
 *   capturedImage: currently captured image URL (to show preview)
 *   onRetake(): clear the captured image
 */
export default function WebcamCapture({ onCapture, capturedImage, onRetake }) {
  const webcamRef = useRef(null)

  const capture = useCallback(() => {
    const canvas = webcamRef.current?.getCanvas()
    if (!canvas) return
    canvas.toBlob((blob) => {
      if (blob) onCapture(blob)
    }, 'image/jpeg', 0.92)
  }, [onCapture])

  if (capturedImage) {
    return (
      <div style={{ textAlign: 'center' }}>
        <div className="webcam-wrapper">
          <img src={capturedImage} alt="Captured face" style={{ width: '100%', display: 'block' }} />
        </div>
        <button className="btn btn--ghost btn--sm mt-md" onClick={onRetake}>
          🔄 Retake photo
        </button>
      </div>
    )
  }

  return (
    <div style={{ textAlign: 'center' }}>
      <div className="webcam-wrapper">
        <Webcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          videoConstraints={{ width: 480, height: 360, facingMode: 'user' }}
          mirrored
          style={{ width: '100%' }}
        />
      </div>
      <button
        id="webcam-capture-btn"
        className="btn btn--primary btn--lg mt-md"
        onClick={capture}
      >
        📸 Capture Photo
      </button>
    </div>
  )
}
