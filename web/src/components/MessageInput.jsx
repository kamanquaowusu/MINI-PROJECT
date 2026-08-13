import { COLORS } from '../theme';

export function MessageInput({ value, onChange, onSubmit, onClear, disabled, variant = 'mobile' }) {
  const isDesktop = variant === 'desktop';

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${COLORS.border}`,
        borderRadius: 24,
        padding: isDesktop ? 20 : 18,
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        boxShadow: '0 4px 16px rgba(15,23,42,0.05)',
      }}
    >
      <label
        htmlFor="sm-message-input"
        style={{
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          fontSize: 13,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: COLORS.text500,
        }}
      >
        The message
      </label>
      <textarea
        id="sm-message-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Paste the message you received…"
        maxLength={1600}
        rows={isDesktop ? 7 : 5}
        style={{
          minHeight: isDesktop ? 180 : 140,
          border: 'none',
          resize: 'vertical',
          fontSize: 16,
          lineHeight: 1.5,
          color: COLORS.text700,
          outline: 'none',
          fontFamily: "'DM Sans', sans-serif",
        }}
      />
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || value.trim().length === 0}
          className="sm-btn sm-btn-primary"
          style={{
            flex: isDesktop ? 'none' : 1,
            width: isDesktop ? 'auto' : '100%',
            padding: isDesktop ? '16px 34px' : '19px',
            background: disabled || value.trim().length === 0 ? '#9BBFBB' : COLORS.teal,
            fontSize: isDesktop ? 16 : 17,
          }}
        >
          Check message
        </button>
        {isDesktop && (
          <button
            type="button"
            onClick={onClear}
            className="sm-btn sm-btn-secondary"
            style={{ padding: '16px 24px', fontSize: 16 }}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
