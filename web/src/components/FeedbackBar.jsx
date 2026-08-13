import { COLORS } from '../theme';

export function FeedbackBar({ status, onHelpful, onNotHelpful }) {
  if (status === 'done') {
    return (
      <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 14, color: COLORS.text500, padding: '0 2px' }}>
        Thanks — recorded. This helps the pilot.
      </div>
    );
  }

  const disabled = status === 'sending';

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '0 2px' }}>
      <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 14, color: COLORS.text500 }}>Was this helpful?</span>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          onClick={onHelpful}
          disabled={disabled}
          style={{
            border: `1px solid ${COLORS.border}`,
            background: '#FFFFFF',
            color: COLORS.text900,
            padding: '10px 18px',
            borderRadius: 999,
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          Yes
        </button>
        <button
          type="button"
          onClick={onNotHelpful}
          disabled={disabled}
          style={{
            border: `1px solid ${COLORS.border}`,
            background: '#FFFFFF',
            color: COLORS.text500,
            padding: '10px 18px',
            borderRadius: 999,
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          No, report
        </button>
      </div>
    </div>
  );
}
