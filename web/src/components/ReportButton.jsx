export function ReportButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="sm-btn sm-btn-danger"
      style={{ marginTop: 2, width: '100%', padding: 14, fontSize: 16 }}
    >
      Report this message
    </button>
  );
}
