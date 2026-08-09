import './SubjectCard.css'

/**
 * SubjectCard — matches the original Streamlit subject_card component.
 * Props:
 *   name, code, section, stats (array of {icon, label, value}), footer (ReactNode)
 */
export default function SubjectCard({ name, code, section, stats = [], footer }) {
  return (
    <div className="subject-card">
      <div className="subject-card__header">
        <div>
          <h3 className="subject-card__name">{name}</h3>
          <p className="subject-card__meta">
            <span className="subject-card__code">{code}</span>
            {section && <span className="subject-card__section"> · {section}</span>}
          </p>
        </div>
      </div>

      {stats.length > 0 && (
        <div className="subject-card__stats">
          {stats.map(({ icon, label, value }) => (
            <div key={label} className="stat">
              <span className="stat__icon">{icon}</span>
              <span className="stat__value">{value}</span>
              <span className="stat__label">{label}</span>
            </div>
          ))}
        </div>
      )}

      {footer && (
        <div className="subject-card__footer">
          <hr className="divider" />
          {footer}
        </div>
      )}
    </div>
  )
}
