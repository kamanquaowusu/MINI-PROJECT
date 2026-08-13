import { ShieldIcon } from './icons';
import { COLORS } from '../theme';

export function CheckingScreen() {
  return (
    <div
      style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 22 }}
      role="status"
      aria-busy="true"
      aria-live="polite"
    >
      <div
        className="pulse-circle"
        style={{
          width: 96,
          height: 96,
          borderRadius: 999,
          background: '#DCEAE8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <ShieldIcon size={42} stroke={COLORS.teal} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, textAlign: 'center' }}>
        <div style={{ fontFamily: "'Bricolage Grotesque', sans-serif", fontWeight: 700, fontSize: 26, lineHeight: 1.15, color: COLORS.text900 }}>
          Checking…
        </div>
        <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 15, lineHeight: 1.45, color: COLORS.text500, maxWidth: 250 }}>
          Reading the message for known scam signs. This takes a moment.
        </div>
      </div>
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div className="shimmer-bar" style={{ height: 14, borderRadius: 999 }} />
        <div className="shimmer-bar" style={{ height: 14, width: '78%', borderRadius: 999 }} />
        <div className="shimmer-bar" style={{ height: 14, width: '54%', borderRadius: 999 }} />
      </div>
    </div>
  );
}
