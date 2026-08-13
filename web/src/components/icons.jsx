// SVG paths copied from the approved design markup ("Sika Shield.dc.html")
// so icon shapes match exactly. Distinct shape per risk band (circle /
// triangle / octagon) so risk never relies on colour alone.

export function ShieldIcon({ size = 20, stroke = '#fff' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l7 3v6c0 4.4-3 8-7 9-4-1-7-4.6-7-9V6z" />
      <path d="M9.2 12.2l2 2 3.6-4" />
    </svg>
  );
}

export function CircleCheckIcon({ size = 28, stroke = '#15803D' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.4l2.6 2.6L16 9.6" />
    </svg>
  );
}

export function TriangleAlertIcon({ size = 28, stroke = '#B45309' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.3 3.9L2.9 17.1A1.9 1.9 0 004.6 20h14.8a1.9 1.9 0 001.7-2.9L13.7 3.9a1.9 1.9 0 00-3.4 0z" />
      <path d="M12 9v4" />
      <circle cx="12" cy="16.4" r="0.6" fill={stroke} />
    </svg>
  );
}

export function OctagonXIcon({ size = 28, stroke = '#DC2626' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.6 3h6.8L21 8.6v6.8L15.4 21H8.6L3 15.4V8.6z" />
      <path d="M9.4 9.4l5.2 5.2M14.6 9.4l-5.2 5.2" />
    </svg>
  );
}

export function CheckMarkIcon({ size = 18, stroke = '#15803D' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.6l4 4 10-10" />
    </svg>
  );
}

export function XMarkIcon({ size = 18, stroke = '#DC2626' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

export function DotIcon({ size = 7, fill = '#B45309' }) {
  return <span style={{ width: size, height: size, borderRadius: 999, background: fill, display: 'inline-block' }} />;
}

export function InfoCircleIcon({ size = 18, stroke = '#0F766E' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.9" strokeLinecap="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 7.6v.6" />
    </svg>
  );
}

export function EyeIcon({ size = 17, stroke = '#B45309' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round">
      <path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" />
      <circle cx="12" cy="12" r="2.4" />
    </svg>
  );
}

export function ChevronDownIcon({ size = 14, stroke = '#5A6472' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

export const BAND_ICON = {
  safe: CircleCheckIcon,
  suspicious: TriangleAlertIcon,
};
