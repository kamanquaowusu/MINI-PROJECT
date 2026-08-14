import { ShieldIcon } from './icons';
import { COLORS } from '../theme';

export function BrandHeader({ variant = 'mobile', onHome }) {
  const tileSize = variant === 'desktop' ? 34 : 36;
  const nameSize = variant === 'desktop' ? 19 : 17;

  // With onHome the whole lockup becomes the "go home" control, so it must
  // be a real <button> (keyboard-reachable, announced as a control) rather
  // than a div with a click handler.
  const Tag = onHome ? 'button' : 'div';
  const interactiveProps = onHome
    ? {
        type: 'button',
        onClick: onHome,
        'aria-label': 'SafeMoMo — back to home',
        className: 'sm-brand-home',
      }
    : {};

  return (
    <Tag
      {...interactiveProps}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: variant === 'desktop' ? 0 : '12px 20px 16px',
        ...(onHome
          ? { background: 'none', border: 0, textAlign: 'left', cursor: 'pointer', font: 'inherit' }
          : {}),
      }}
    >
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
    </Tag>
  );
}
