import { COLORS } from '../theme';

export function MessagePreview({ text }) {
  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${COLORS.border}`,
        borderRadius: 16,
        padding: '12px 14px',
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 13,
        lineHeight: 1.45,
        color: COLORS.text500,
      }}
    >
      "{text.length > 220 ? `${text.slice(0, 220)}…` : text}"
    </div>
  );
}
