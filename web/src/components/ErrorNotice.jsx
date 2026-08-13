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
          className="sm-btn sm-btn-secondary"
          style={{ alignSelf: 'flex-start', padding: '8px 16px', fontSize: 13 }}
        >
          Try again
        </button>
      )}
    </div>
  );
}
