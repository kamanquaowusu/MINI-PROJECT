import { ShieldIcon } from './icons';
import { COLORS } from '../theme';

export function BrandHeader({ variant = 'mobile' }) {
  const tileSize = variant === 'desktop' ? 34 : 36;
  const nameSize = variant === 'desktop' ? 19 : 17;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: variant === 'desktop' ? 0 : '12px 20px 16px' }}>
      <div
        style={{
          width: tileSize,
          height: tileSize,
          borderRadius: 12,
          background: COLORS.teal,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flex: 'none',
        }}
      >
        <ShieldIcon size={variant === 'desktop' ? 19 : 20} stroke="#fff" />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <div
          style={{
            fontFamily: "'Bricolage Grotesque', sans-serif",
            fontWeight: 700,
            fontSize: nameSize,
            lineHeight: 1,
            letterSpacing: '-0.01em',
            color: COLORS.text900,
          }}
        >
          SafeMoMo
        </div>
        {variant !== 'desktop' && (
          <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 12, color: COLORS.text400 }}>
            Independent · not linked to any network
          </div>
        )}
      </div>
    </div>
  );
}
