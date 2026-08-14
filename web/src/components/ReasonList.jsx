import { CheckMarkIcon, XMarkIcon } from './icons';
import { BAND_THEME, COLORS } from '../theme';

function BulletIcon({ reasonKind }) {
  if (reasonKind === 'clear') return <CheckMarkIcon size={18} stroke="#15803D" />;
  return <XMarkIcon size={18} stroke="#DC2626" />;
}

export function ReasonList({ band, reasons }) {
  const theme = BAND_THEME[band];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div
        style={{
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: COLORS.text400,
        }}
      >
        {theme.reasonsTitle}
      </div>
      {reasons.map((r) => (
        <div key={r.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          <span style={{ flex: 'none', marginTop: 2 }}>
            <BulletIcon reasonKind={r.kind} />
          </span>
          <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 15, lineHeight: 1.45, color: COLORS.text700 }}>
            {r.text}
          </span>
        </div>
      ))}
    </div>
  );
}
