/**
 * Generic Modal wrapper.
 * Usage:
 *   <Modal title="My Modal" onClose={() => setOpen(false)}>
 *     ...content...
 *   </Modal>
 */
export default function Modal({ title, onClose, children, maxWidth = '540px' }) {
  // Close on backdrop click
  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdrop}>
      <div className="modal" style={{ maxWidth }} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal__header">
          <h2 className="modal__title">{title}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
