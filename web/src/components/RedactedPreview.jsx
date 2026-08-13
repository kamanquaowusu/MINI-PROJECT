import { useState } from 'react';
import { ChevronDownIcon } from './icons';
import { COLORS } from '../theme';

// Not in the mockup -- the on-screen proof that a consented-to log entry was
// actually redacted before being saved, per PDF §8.4's consent requirement.
export function RedactedPreview({ text }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ border: `1px solid ${COLORS.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="sm-hoverable"
        style={{
          width: '100%',
          border: 0,
          background: '#FFFFFF',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          fontSize: 13,
          color: COLORS.text500,
        }}
      >
        <span>What we saved</span>
        <span style={{ transform: open ? 'rotate(180deg)' : 'none', display: 'inline-flex' }}>
          <ChevronDownIcon />
        </span>
      </button>
      {open && (
        <div
          style={{
            padding: '10px 14px 14px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 13,
            lineHeight: 1.5,
            color: COLORS.text700,
            background: '#F7F9FA',
            wordBreak: 'break-word',
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
}
