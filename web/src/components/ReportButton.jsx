export function ReportButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="sm-btn sm-btn-danger"
      style={{
        marginTop: 2,
        width: '100%',
        padding: 14,
        background: disabled ? '#E9A6A6' : '#DC2626',
        fontSize: 16,
      }}
    >
      Report this message
    </button>
  );
}
