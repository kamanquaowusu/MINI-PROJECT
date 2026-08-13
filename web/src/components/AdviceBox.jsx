import { COLORS } from '../theme';

export function AdviceBox({ title, text }) {
  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${COLORS.border}`,
        borderRadius: 24,
        padding: '14px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      <div
        style={{
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          fontSize: 13,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: COLORS.text500,
        }}
      >
        {title}
      </div>
      <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 15, lineHeight: 1.45, color: COLORS.text700 }}>
        {text}
      </div>
    </div>
  );
}
