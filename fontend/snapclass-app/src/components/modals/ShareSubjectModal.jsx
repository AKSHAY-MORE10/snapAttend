import { useState } from 'react'
import Modal from '../Modal'
import { useToast } from '../../context/ToastContext'

export default function ShareSubjectModal({ subjectName, subjectCode, onClose }) {
  const toast = useToast()
  const [copied, setCopied] = useState(false)

  const shareUrl = `${window.location.origin}/student?join-code=${subjectCode}`

  const copyCode = async () => {
    await navigator.clipboard.writeText(subjectCode)
    setCopied(true)
    toast('Code copied to clipboard!', 'success')
    setTimeout(() => setCopied(false), 2000)
  }

  const copyLink = async () => {
    await navigator.clipboard.writeText(shareUrl)
    toast('Join link copied!', 'success')
  }

  return (
    <Modal title="Share Subject" onClose={onClose}>
      <p style={{ marginBottom: 'var(--space-lg)' }}>
        Share this code or link with your students so they can enroll in{' '}
        <strong style={{ color: 'var(--color-text-primary)' }}>{subjectName}</strong>.
      </p>

      <div style={{
        background: 'var(--color-surface-hi)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-xl)',
        textAlign: 'center',
        border: '1px solid var(--color-border-hi)',
        marginBottom: 'var(--space-lg)',
      }}>
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-dim)', marginBottom: 'var(--space-sm)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Subject Code
        </p>
        <p style={{ fontFamily: 'var(--font-display)', fontSize: '3rem', color: 'var(--color-text-primary)', letterSpacing: '0.1em', margin: 0 }}>
          {subjectCode}
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        <button
          id="copy-code-btn"
          className="btn btn--primary btn--stretch"
          onClick={copyCode}
        >
          {copied ? '✓ Copied!' : '📋 Copy Code'}
        </button>
        <button
          id="copy-link-btn"
          className="btn btn--ghost btn--stretch"
          onClick={copyLink}
        >
          🔗 Copy Join Link
        </button>
      </div>

      <p style={{ fontSize: '0.8rem', color: 'var(--color-text-dim)', marginTop: 'var(--space-md)', textAlign: 'center' }}>
        Students can also visit: <code style={{ color: 'var(--color-accent)' }}>{shareUrl}</code>
      </p>
    </Modal>
  )
}
