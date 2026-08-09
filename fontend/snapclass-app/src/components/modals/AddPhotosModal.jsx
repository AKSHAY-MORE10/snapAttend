import { useRef, useState } from 'react'
import Modal from '../Modal'

/**
 * AddPhotosModal — lets teacher add multiple classroom photos.
 * Calls onAdd(files[]) with new File objects.
 */
export default function AddPhotosModal({ onClose, onAdd }) {
  const inputRef = useRef(null)
  const [previews, setPreviews] = useState([])

  const handleFiles = (e) => {
    const files = Array.from(e.target.files)
    if (!files.length) return

    const newPreviews = files.map(f => ({
      file: f,
      url: URL.createObjectURL(f),
      name: f.name,
    }))
    setPreviews(prev => [...prev, ...newPreviews])
  }

  const removePreview = (idx) => {
    setPreviews(prev => {
      URL.revokeObjectURL(prev[idx].url)
      return prev.filter((_, i) => i !== idx)
    })
  }

  const handleAdd = () => {
    if (previews.length) {
      onAdd(previews.map(p => p.file))
    }
    onClose()
  }

  return (
    <Modal title="Add Classroom Photos" onClose={onClose} maxWidth="600px">
      <p style={{ marginBottom: 'var(--space-lg)' }}>
        Upload one or more classroom photos. AI will scan each photo for enrolled students.
      </p>

      <button
        id="choose-photos-btn"
        className="btn btn--secondary btn--stretch"
        onClick={() => inputRef.current?.click()}
        style={{ marginBottom: 'var(--space-md)' }}
      >
        📂 Choose Photos
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        style={{ display: 'none' }}
        onChange={handleFiles}
      />

      {previews.length > 0 && (
        <>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>
            {previews.length} photo{previews.length !== 1 ? 's' : ''} selected
          </p>
          <div className="photo-gallery" style={{ marginBottom: 'var(--space-lg)' }}>
            {previews.map((p, i) => (
              <div key={i} className="photo-gallery__item">
                <img src={p.url} alt={`Preview ${i + 1}`} />
                <button
                  className="remove-btn"
                  onClick={() => removePreview(i)}
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      {previews.length === 0 && (
        <div className="empty-state" style={{ padding: 'var(--space-xl)', marginBottom: 'var(--space-lg)' }}>
          <div className="empty-state__icon">🖼️</div>
          <p className="empty-state__text">No photos selected yet</p>
        </div>
      )}

      <div className="flex gap-md">
        <button className="btn btn--ghost btn--stretch" onClick={onClose}>Cancel</button>
        <button
          id="add-photos-confirm-btn"
          className="btn btn--primary btn--stretch"
          onClick={handleAdd}
          disabled={previews.length === 0}
        >
          ✓ Add {previews.length > 0 ? `${previews.length} Photo${previews.length !== 1 ? 's' : ''}` : 'Photos'}
        </button>
      </div>
    </Modal>
  )
}
