export function ProgressDots({ activeIndex = null, color = '#0F766E', shimmer = false }) {
  return (
    <div style={{ display: 'flex', gap: 8 }} aria-hidden="true">
      {[0, 1].map((i) => {
        const isActive = activeIndex === i;
        const style = {
          flex: 1,
          height: 8,
          borderRadius: 999,
          background: isActive ? color : '#E3E8ED',
        };
        return <div key={i} className={shimmer ? 'shimmer-bar' : undefined} style={style} />;
      })}
    </div>
  );
}
