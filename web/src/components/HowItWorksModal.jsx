import { Modal } from './Modal';
import { COLORS } from '../theme';

const STEPS = [
  {
    title: 'Paste the message',
    text: 'Copy the SMS or MoMo prompt you received and paste it into the input box. Nothing is sent anywhere until you press "Check message".',
  },
  {
    title: 'We scan it',
    text: 'The message is normalised (to catch disguised or hidden characters) and scored by a model trained to recognise common MoMo scam patterns — PIN requests, fake reversals, prize promos, and odd links.',
  },
  {
    title: 'You get a plain-language result',
    text: 'We show a risk band — Safe or Suspicious — along with the specific reasons behind it, so you understand why, not just what.',
  },
  {
    title: 'You decide',
    text: 'The result is advisory only, never a verdict. When in doubt, contact your provider directly before acting on any message.',
  },
];

export function HowItWorksModal({ open, onClose }) {
  return (
    <Modal open={open} onClose={onClose} title="How it works">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        {STEPS.map((step, i) => (
          <div key={step.title} style={{ display: 'flex', gap: 14 }}>
            <div
              style={{
                flex: 'none',
                width: 28,
                height: 28,
                borderRadius: 999,
                background: COLORS.tealTint,
                border: `1px solid ${COLORS.tealBorder}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: "'DM Sans', sans-serif",
                fontWeight: 700,
                fontSize: 13,
                color: COLORS.teal,
              }}
            >
              {i + 1}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div
                style={{
                  fontFamily: "'DM Sans', sans-serif",
                  fontWeight: 600,
                  fontSize: 15,
                  color: COLORS.text900,
                }}
              >
                {step.title}
              </div>
              <p style={{ margin: 0, fontFamily: "'DM Sans', sans-serif", fontSize: 14, lineHeight: 1.5, color: COLORS.text500 }}>
                {step.text}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
}
