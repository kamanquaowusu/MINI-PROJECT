import { COLORS } from '../theme';

const TAGS = ['PIN requests', 'Fake reversals', 'Prize promos', 'Odd links', 'Hidden characters'];

export function WhatWeLookFor() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div
        style={{
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: COLORS.text300,
        }}
      >
        What we look for
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {TAGS.map((tag) => (
          <span
            key={tag}
            style={{
              background: '#FFFFFF',
              border: `1px solid ${COLORS.border}`,
              borderRadius: 999,
              padding: '9px 14px',
              fontFamily: "'DM Sans', sans-serif",
              fontWeight: 500,
              fontSize: 13,
              color: COLORS.text600,
            }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
