import { BAND_ICON } from './icons';
import { ReasonList } from './ReasonList';
import { ObfuscationCallout } from './ObfuscationCallout';
import { BAND_THEME, COLORS } from '../theme';

export function ResultCard({ band, reasons, obfuscationSuspected, variant = 'mobile' }) {
  const theme = BAND_THEME[band];
  const Icon = BAND_ICON[band];
  const isDesktop = variant === 'desktop';
  const iconSize = isDesktop ? 56 : 52;

  return (
    <section
      role="status"
      aria-live="polite"
      style={{
        background: '#FFFFFF',
        border: `2px solid ${theme.accent}`,
        borderRadius: 24,
        padding: isDesktop ? 24 : 18,
        display: 'flex',
        flexDirection: 'column',
        gap: isDesktop ? 16 : 12,
        boxShadow: theme.shadow,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: isDesktop ? 16 : 14 }}>
        <div
          style={{
            width: iconSize,
            height: iconSize,
            borderRadius: 16,
            background: theme.tint,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 'none',
          }}
        >
          <Icon size={isDesktop ? 30 : 28} stroke={theme.accent} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: isDesktop ? 6 : 5 }}>
          <div
            style={{
              fontFamily: "'DM Sans', sans-serif",
              fontWeight: 600,
              fontSize: 11,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: theme.accent,
            }}
          >
            {theme.riskLabel}
          </div>
          <div
            style={{
              fontFamily: "'Bricolage Grotesque', sans-serif",
              fontWeight: 800,
              fontSize: isDesktop ? 36 : 32,
              lineHeight: 1,
              letterSpacing: '-0.02em',
              color: theme.headingColor,
            }}
          >
            {theme.headline}
          </div>
        </div>
      </div>

      <p style={{ margin: 0, fontFamily: "'DM Sans', sans-serif", fontWeight: 500, fontSize: isDesktop ? 17 : 16, lineHeight: 1.4, color: COLORS.text800 }}>
        {theme.summary}
      </p>

      <ReasonList band={band} reasons={reasons} />

      {band === 'suspicious' && obfuscationSuspected && <ObfuscationCallout />}
    </section>
  );
}
