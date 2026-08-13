import { EyeIcon } from './icons';
import { COLORS } from '../theme';

export function ObfuscationCallout() {
  return (
    <div
      style={{
        background: COLORS.obfuscationBg,
        border: `1px solid ${COLORS.obfuscationBorder}`,
        borderRadius: 16,
        padding: '12px 14px',
        display: 'flex',
        gap: 10,
        alignItems: 'flex-start',
      }}
    >
      <span style={{ flex: 'none', marginTop: 2 }}>
        <EyeIcon size={17} stroke={COLORS.obfuscationStrong} />
      </span>
      <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, lineHeight: 1.45, color: COLORS.obfuscationText }}>
        <strong style={{ fontWeight: 600, color: COLORS.obfuscationStrong }}>Hidden characters found.</strong>{' '}
        This message uses disguised or invisible letters — a common scam trick.
      </div>
    </div>
  );
}
