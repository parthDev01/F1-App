const TYRE_COLORS = { S: '#E8002D', M: '#FFD700', H: '#ccc', I: '#39b54a', W: '#0067ff', '?': '#666' }
const TYRE_TEXT   = { S: '#fff',    M: '#000',    H: '#111', I: '#fff',     W: '#fff',    '?': '#fff' }

export function WinProbBars({ drivers, probabilities, onDriverClick, selectedDriver }) {
  const winProbs = probabilities?.win || {}
  const top = drivers
    ?.filter(d => (winProbs[d.driver_number] || 0) >= 0.5)
    ?.sort((a, b) => (winProbs[b.driver_number] || 0) - (winProbs[a.driver_number] || 0))
    || []

  return (
    <div>
      {top.map(d => {
        const pct = winProbs[d.driver_number] || 0
        const isSel = selectedDriver === d.driver_number
        return (
          <div
            key={d.driver_number}
            onClick={() => onDriverClick(d.driver_number)}
            style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '5px 12px',
              background: isSel ? 'rgba(232,0,45,0.08)' : 'transparent',
              cursor: 'pointer',
              transition: 'background 0.1s',
            }}
          >
            <span style={{ fontFamily: 'var(--M)', fontSize: 12, width: 30, color: d.color, fontWeight: 700 }}>{d.short_name}</span>
            <div style={{ flex: 1, height: 16, background: '#1a1a1a', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                height: '100%', width: `${pct}%`, background: d.color,
                borderRadius: 3, minWidth: 2,
                transition: 'width 0.6s ease',
                display: 'flex', alignItems: 'center', paddingLeft: 5,
              }}>
                {pct >= 8 && (
                  <span style={{ fontFamily: 'var(--M)', fontSize: 10, fontWeight: 700, color: '#000', opacity: 0.8 }}>{pct}%</span>
                )}
              </div>
            </div>
            <span style={{ fontFamily: 'var(--M)', fontSize: 11, color: 'rgba(255,255,255,0.4)', width: 32, textAlign: 'right' }}>
              {pct < 8 ? `${pct}%` : ''}
            </span>
          </div>
        )
      })}
      <div style={{ padding: '4px 12px', fontSize: 9, fontFamily: 'var(--M)', color: 'rgba(255,255,255,0.18)', marginTop: 2 }}>
        pos × pace × tyre × strategy × SC model
      </div>
    </div>
  )
}


export function IncidentGauges({ probabilities }) {
  const sc  = probabilities?.sc_prob  || 0
  const rf  = probabilities?.rf_prob  || 0
  const vsc = probabilities?.vsc_prob || 0

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, padding: '8px 12px' }}>
      {[
        { label: 'Safety Car', value: sc,  color: '#FF9800' },
        { label: 'Red Flag',   value: rf,  color: '#f44336' },
        { label: 'VSC',        value: vsc, color: '#4CAF50' },
      ].map(g => (
        <div key={g.label} style={{
          background: 'var(--c3)', border: '1px solid var(--brd)', borderRadius: 6,
          padding: '8px 10px', textAlign: 'center',
        }}>
          <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--mut)', marginBottom: 3 }}>{g.label}</div>
          <div style={{ fontFamily: 'var(--M)', fontSize: 20, fontWeight: 700, color: g.color }}>{g.value}%</div>
          <div style={{ width: '100%', height: 3, background: '#222', borderRadius: 2, marginTop: 4, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${g.value}%`, background: g.color, borderRadius: 2, transition: 'width 0.5s' }} />
          </div>
        </div>
      ))}
    </div>
  )
}


export function PodiumBars({ drivers, probabilities, onDriverClick }) {
  const podProbs = probabilities?.podium || {}
  const top6 = drivers?.slice(0, 6) || []
  const medals = ['🥇', '🥈', '🥉', '4.', '5.', '6.']

  return (
    <div>
      {top6.map((d, i) => {
        const pct = podProbs[d.driver_number] || 0
        return (
          <div
            key={d.driver_number}
            onClick={() => onDriverClick(d.driver_number)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '5px 12px', cursor: 'pointer',
              borderBottom: i < 5 ? '1px solid rgba(255,255,255,0.04)' : 'none',
              transition: 'background 0.1s',
            }}
            onMouseEnter={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
            onMouseLeave={e => e.currentTarget.style.background='transparent'}
          >
            <span style={{ fontSize: 13, width: 18 }}>{medals[i]}</span>
            <div style={{ width: 3, height: 20, background: d.color, borderRadius: 2, flexShrink: 0 }} />
            <span style={{ fontSize: 13, fontWeight: 700, width: 32 }}>{d.short_name}</span>
            <div style={{ flex: 1, height: 3, background: '#1e1e1e', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: d.color, borderRadius: 2, transition: 'width 0.6s' }} />
            </div>
            <span style={{ fontFamily: 'var(--M)', fontSize: 11, color: d.color, width: 32, textAlign: 'right' }}>{pct}%</span>
          </div>
        )
      })}
    </div>
  )
}


export function TyreIndicator({ compound, age, small = false }) {
  const color = TYRE_COLORS[compound] || '#666'
  const textColor = TYRE_TEXT[compound] || '#fff'
  const size = small ? 14 : 18

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: color, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: small ? 8 : 10, fontWeight: 700, color: textColor, flexShrink: 0,
      }}>
        {compound}
      </div>
      <span style={{ fontFamily: 'var(--M)', fontSize: small ? 10 : 11, color: 'var(--mut)' }}>{age}L</span>
    </div>
  )
}
