export function ErrorNotice({ message, onRetry }) {
  return (
    <div
      role="alert"
      style={{
        background: '#FDECEC',
        border: '1px solid #F3C6C6',
        borderRadius: 16,
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 14,
        color: '#7A1D1D',
      }}
    >
      <span>Something went wrong checking that message: {message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          style={{
            alignSelf: 'flex-start',
            border: '1px solid #DDE3E9',
            background: '#FFFFFF',
            borderRadius: 999,
            padding: '8px 16px',
            fontWeight: 600,
            fontSize: 13,
          }}
        >
          Try again
        </button>
      )}
    </div>
  );
}
