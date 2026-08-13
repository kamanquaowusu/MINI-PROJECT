import { useEffect, useState } from 'react';
import { checkMessage, sendFeedback } from './api';
import { useMediaQuery } from './useMediaQuery';
import { COLORS } from './theme';

import { BrandHeader } from './components/BrandHeader';
import { TopNav } from './components/TopNav';
import { ProgressDots } from './components/ProgressDots';
import { AdvisoryFooter } from './components/AdvisoryFooter';
import { MessageInput } from './components/MessageInput';
import { WhatWeLookFor } from './components/WhatWeLookFor';
import { ConsentToggle } from './components/ConsentToggle';
import { MessagePreview } from './components/MessagePreview';
import { CheckingScreen } from './components/CheckingScreen';
import { ResultCard } from './components/ResultCard';
import { AdviceBox } from './components/AdviceBox';
import { FeedbackBar } from './components/FeedbackBar';
import { ReportButton } from './components/ReportButton';
import { RedactedPreview } from './components/RedactedPreview';
import { ErrorNotice } from './components/ErrorNotice';
import { HowItWorksModal } from './components/HowItWorksModal';
import { ReportScamModal } from './components/ReportScamModal';

const CONSENT_KEY = 'safemomo_consent';
// Real inference is ~5ms -- without a floor the checking screen is
// unobservable and unscreenshottable. This is a UX floor, not a fake delay.
const MIN_SPINNER_MS = 600;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function App() {
  const isDesktop = useMediaQuery('(min-width: 1024px)');

  const [screen, setScreen] = useState('home'); // home | checking | result | error
  const [message, setMessage] = useState('');
  const [consent, setConsent] = useState(() => localStorage.getItem(CONSENT_KEY) === '1');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [feedbackStatus, setFeedbackStatus] = useState(null); // null | 'sending' | 'done'
  const [howItWorksOpen, setHowItWorksOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(CONSENT_KEY, consent ? '1' : '0');
  }, [consent]);

  async function handleCheck() {
    if (message.trim().length === 0) return;
    setScreen('checking');
    setError(null);
    setFeedbackStatus(null);
    try {
      const [res] = await Promise.all([
        checkMessage({ message, consent }),
        delay(MIN_SPINNER_MS),
      ]);
      setResult(res);
      setScreen('result');
    } catch (e) {
      setError(e.message || 'network error');
      setScreen('error');
    }
  }

  function handleClear() {
    setMessage('');
    setResult(null);
    setScreen('home');
    setFeedbackStatus(null);
  }

  async function submitFeedback(verdict) {
    if (!result) return;
    setFeedbackStatus('sending');
    try {
      await sendFeedback({ checkId: result.check_id, verdict });
      setFeedbackStatus('done');
    } catch {
      setFeedbackStatus(null);
    }
  }

  const variant = isDesktop ? 'desktop' : 'mobile';

  const inputBlock = (
    <>
      <MessageInput
        value={message}
        onChange={setMessage}
        onSubmit={handleCheck}
        onClear={handleClear}
        disabled={screen === 'checking'}
        variant={variant}
      />
      {!isDesktop && <WhatWeLookFor />}
      <ConsentToggle checked={consent} onChange={setConsent} />
    </>
  );

  const resultBlock = result && (
    <>
      <ProgressDots activeIndex={BAND_INDEX[result.band]} color={BAND_COLOR[result.band]} />
      <MessagePreview text={message} />
      <ResultCard
        band={result.band}
        reasons={result.reasons}
        obfuscationSuspected={result.obfuscation_suspected}
        variant={variant}
      />
      <AdviceBox title={result.advice.title} text={result.advice.text} />
      {result.band === 'suspicious' && <ReportButton onClick={() => setReportOpen(true)} />}
      <FeedbackBar
        status={feedbackStatus}
        onHelpful={() => submitFeedback('helpful')}
        onNotHelpful={() => submitFeedback('not_helpful')}
      />
      {result.logged && result.redacted_preview && <RedactedPreview text={result.redacted_preview} />}
    </>
  );

  const modals = (
    <>
      <HowItWorksModal open={howItWorksOpen} onClose={() => setHowItWorksOpen(false)} />
      <ReportScamModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        initialMessage={message}
        checkId={result?.check_id}
      />
    </>
  );

  if (isDesktop) {
    return (
      <>
        <div className="sm-app">
          <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 24 }}>
            <TopNav onHowItWorks={() => setHowItWorksOpen(true)} onReportScam={() => setReportOpen(true)} />
            <div style={{ padding: 32, display: 'flex', gap: 24, alignItems: 'flex-start' }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <h2 style={{ margin: 0, fontFamily: "'Bricolage Grotesque', sans-serif", fontWeight: 700, fontSize: 34, letterSpacing: '-0.02em', color: COLORS.text900 }}>
                    Check a MoMo message
                  </h2>
                  <p style={{ margin: 0, maxWidth: 460, fontFamily: "'DM Sans', sans-serif", fontSize: 16, lineHeight: 1.5, color: COLORS.text500 }}>
                    Paste a text you're unsure about and we'll tell you how risky it looks — in plain words.
                  </p>
                </div>
                {inputBlock}
                <AdvisoryFooter />
              </div>
              <div style={{ width: 520, display: 'flex', flexDirection: 'column', gap: 16 }}>
                {screen === 'checking' && <CheckingScreen />}
                {screen === 'error' && <ErrorNotice message={error} onRetry={handleCheck} />}
                {screen === 'result' && resultBlock}
                {screen === 'home' && (
                  <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 14, color: COLORS.text400, textAlign: 'center', marginTop: 40 }}>
                    Your result will appear here.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
        {modals}
      </>
    );
  }

  return (
    <>
      <div className="sm-card" style={{ minHeight: '100vh', maxWidth: 480 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 24px 6px', fontFamily: "'DM Sans', sans-serif", fontWeight: 600, fontSize: 13, color: COLORS.text900 }}>
          <span>SafeMoMo</span>
          <span style={{ color: COLORS.text400, fontSize: 11 }}>Pilot</span>
        </div>
        <BrandHeader />
        <div className="sm-screen-body">
          {screen === 'home' && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <h2 style={{ margin: 0, fontFamily: "'Bricolage Grotesque', sans-serif", fontWeight: 700, fontSize: 30, lineHeight: 1.12, letterSpacing: '-0.015em', color: COLORS.text900 }}>
                  Check a MoMo message
                </h2>
                <p style={{ margin: 0, fontFamily: "'DM Sans', sans-serif", fontSize: 15, lineHeight: 1.5, color: COLORS.text500 }}>
                  Paste a text you're unsure about and we'll tell you how risky it looks — in plain words.
                </p>
              </div>
              <ProgressDots activeIndex={null} />
              {inputBlock}
            </>
          )}

          {screen === 'checking' && (
            <>
              <ProgressDots activeIndex={null} shimmer />
              <CheckingScreen />
            </>
          )}

          {screen === 'error' && <ErrorNotice message={error} onRetry={handleCheck} />}

          {screen === 'result' && resultBlock}

          <AdvisoryFooter />
        </div>
      </div>
      {modals}
    </>
  );
}

const BAND_INDEX = { safe: 0, suspicious: 1 };
const BAND_COLOR = { safe: '#15803D', suspicious: '#B45309' };
