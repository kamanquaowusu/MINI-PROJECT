// Design tokens extracted directly from the approved Claude Design markup
// ("Sika Shield.dc.html", Turn 2 / "Daylight" full screen set) -- not
// re-derived. See the implementation plan for the source file reference.

export const COLORS = {
  bg: '#F4F6F8',
  card: '#FFFFFF',
  border: '#DDE3E9',
  teal: '#0F766E',
  tealTint: '#EAF3F2',
  tealBorder: '#C9E0DD',
  tealText: '#25514D',
  text900: '#0B0B0E',
  text800: '#111827',
  text700: '#2B3440',
  text600: '#3F4956',
  text500: '#5A6472',
  text400: '#6B7280',
  text300: '#8A93A0',
  placeholder: '#9AA4B2',
  obfuscationBg: '#FEF6E7',
  obfuscationBorder: '#F3D9A4',
  obfuscationText: '#7A4E10',
  obfuscationStrong: '#B45309',
};

export const BAND_THEME = {
  safe: {
    dotIndex: 0,
    accent: '#15803D',
    headingColor: '#15803D',
    tint: '#E6F4EA',
    shadow: '0 6px 20px rgba(21,128,61,0.08)',
    riskLabel: 'Risk level · low',
    headline: 'Safe',
    summary: 'No obvious signs of a scam were found.',
    icon: 'circleCheck',
    bulletIcon: 'check',
    reasonsTitle: 'What we checked',
  },
  suspicious: {
    dotIndex: 1,
    accent: '#B45309',
    headingColor: '#92400E',
    tint: '#FDF0DC',
    shadow: '0 6px 20px rgba(180,83,9,0.08)',
    riskLabel: 'Risk level · high',
    headline: 'Suspicious',
    summary: 'Strong signs of a scam. Do not act on this message.',
    icon: 'triangleAlert',
    bulletIcon: 'dot',
    reasonsTitle: 'Why',
  },
};
