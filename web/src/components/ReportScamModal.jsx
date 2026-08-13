import { useEffect, useState } from 'react';
import { Modal } from './Modal';
import { COLORS } from '../theme';
import { submitReport } from '../api';

const fieldStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: 14,
  padding: '12px 14px',
  fontSize: 15,
  color: COLORS.text700,
  outline: 'none',
  fontFamily: "'DM Sans', sans-serif",
  width: '100%',
};

const labelStyle = {
  fontFamily: "'DM Sans', sans-serif",
  fontWeight: 600,
  fontSize: 13,
  color: COLORS.text500,
};

export function ReportScamModal({ open, onClose, initialMessage = '', checkId }) {
  const [message, setMessage] = useState(initialMessage);
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState(null); // null | 'sending' | 'done' | 'error'
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      setMessage(initialMessage);
      setPhone('');
      setEmail('');
      setStatus(null);
      setError(null);
    }
  }, [open, initialMessage]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (message.trim().length === 0) return;
    setStatus('sending');
    setError(null);
    try {
      await submitReport({ message, phone, email, checkId });
      setStatus('done');
    } catch (err) {
      setError(err.message || 'network error');
      setStatus('error');
    }
  }

  if (status === 'done') {
    return (
      <Modal open={open} onClose={onClose} title="Report a scam">
        <p style={{ margin: 0, fontFamily: "'DM Sans', sans-serif", fontSize: 15, lineHeight: 1.5, color: COLORS.text700 }}>
          Thanks — your report has been received. Our team will review it.
        </p>
        <button
          type="button"
          onClick={onClose}
          className="sm-btn sm-btn-primary"
          style={{ alignSelf: 'flex-start', padding: '12px 24px', fontSize: 15 }}
        >
          Close
        </button>
      </Modal>
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Report a scam">
      <p style={{ margin: 0, fontFamily: "'DM Sans', sans-serif", fontSize: 14, lineHeight: 1.5, color: COLORS.text500 }}>
        Tell us about the message. Your phone number and email are optional, but help us follow up if needed.
      </p>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={labelStyle}>Message</span>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Paste the scam message…"
            required
            maxLength={1600}
            rows={5}
            className="sm-field"
            style={{ ...fieldStyle, resize: 'vertical', lineHeight: 1.5 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={labelStyle}>Your phone number (optional)</span>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="e.g. 024 123 4567"
            className="sm-field"
            style={fieldStyle}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={labelStyle}>Your email (optional)</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="sm-field"
            style={fieldStyle}
          />
        </label>
        {status === 'error' && (
          <div role="alert" style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: '#B91C1C' }}>
            Couldn't send that report: {error}. Please try again.
          </div>
        )}
        <button
          type="submit"
          disabled={status === 'sending' || message.trim().length === 0}
          className="sm-btn sm-btn-danger"
          style={{
            padding: 14,
            background: status === 'sending' || message.trim().length === 0 ? '#E9A6A6' : '#DC2626',
            fontSize: 16,
          }}
        >
          {status === 'sending' ? 'Sending…' : 'Submit report'}
        </button>
      </form>
    </Modal>
  );
}
