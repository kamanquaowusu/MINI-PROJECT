import { BrandHeader } from './BrandHeader';
import { COLORS } from '../theme';

export function TopNav() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '20px 32px',
        background: '#FFFFFF',
        borderBottom: `1px solid ${COLORS.border}`,
        borderRadius: '24px 24px 0 0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <BrandHeader variant="desktop" />
        <span
          style={{
            marginLeft: 4,
            background: COLORS.tealTint,
            border: `1px solid ${COLORS.tealBorder}`,
            borderRadius: 999,
            padding: '5px 10px',
            fontFamily: "'DM Sans', sans-serif",
            fontWeight: 600,
            fontSize: 11,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: COLORS.teal,
          }}
        >
          Pilot
        </span>
      </div>
      <nav style={{ display: 'flex', gap: 24, fontFamily: "'DM Sans', sans-serif", fontWeight: 500, fontSize: 15, color: COLORS.text500 }}>
        <span>How it works</span>
        <span>Common scams</span>
        <span>Report a scam</span>
      </nav>
    </div>
  );
}
