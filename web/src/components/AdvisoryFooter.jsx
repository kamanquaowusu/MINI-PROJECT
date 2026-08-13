import { InfoCircleIcon } from './icons';
import { COLORS } from '../theme';

// Present on EVERY screen -- a hard requirement (PDF §8.3): the app must
// always make clear the assessment is automated and advisory, never a
// verdict.
export function AdvisoryFooter() {
  return (
    <p
      style={{
        margin: 0,
        marginTop: 'auto',
        display: 'flex',
        gap: 12,
        alignItems: 'flex-start',
        background: COLORS.tealTint,
        border: `1px solid ${COLORS.tealBorder}`,
        borderRadius: 16,
        padding: '14px 16px',
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 13,
        lineHeight: 1.45,
        color: COLORS.tealText,
      }}
    >
      <span style={{ flex: 'none', marginTop: 1 }}>
        <InfoCircleIcon size={18} stroke={COLORS.teal} />
      </span>
      <span>
        This is an automated check to help you decide. It's not a guarantee — use your own
        judgement, and when in doubt contact your provider directly.
      </span>
    </p>
  );
}
