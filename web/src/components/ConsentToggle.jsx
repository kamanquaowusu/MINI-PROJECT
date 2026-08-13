import { COLORS } from '../theme';

// Not in the mockup -- added because PDF §8.4 (Shadow-Mode Validation Loop)
// requires logging to be consent-gated. Default off, persisted so the
// user's choice sticks across visits.
export function ConsentToggle({ checked, onChange }) {
  return (
    <label
      style={{
        display: 'flex',
        gap: 12,
        alignItems: 'flex-start',
        background: '#FFFFFF',
        border: `1px solid ${COLORS.border}`,
        borderRadius: 16,
        padding: '14px 16px',
        cursor: 'pointer',
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ marginTop: 3, width: 18, height: 18, accentColor: COLORS.teal, flex: 'none' }}
      />
      <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, lineHeight: 1.5, color: COLORS.text600 }}>
        Help improve SafeMoMo — save an anonymised copy of this message (phone numbers, amounts
        and names removed) so the pilot can be tested against real messages. Optional.
      </span>
    </label>
  );
}
