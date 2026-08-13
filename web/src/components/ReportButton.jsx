export function ReportButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        marginTop: 2,
        border: 0,
        width: '100%',
        padding: 14,
        borderRadius: 999,
        background: disabled ? '#E9A6A6' : '#DC2626',
        color: '#fff',
        fontWeight: 600,
        fontSize: 16,
      }}
    >
      Report this message
    </button>
  );
}
