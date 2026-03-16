import { useEffect, useState } from 'react'

const TYPE_STYLES = {
  opportunity: { bg: 'rgba(76,175,80,0.12)',  border: 'rgba(76,175,80,0.25)',  badge: 'rgba(76,175,80,0.18)',  text: '#66bb6a', bar: '#66bb6a' },
  risk:        { bg: 'rgba(244,67,54,0.12)',   border: 'rgba(244,67,54,0.25)',  badge: 'rgba(244,67,54,0.18)',  text: '#ef5350', bar: '#ef5350' },
  warning:     { bg: 'rgba(255,152,0,0.12)',   border: 'rgba(255,152,0,0.25)',  badge: 'rgba(255,152,0,0.18)',  text: '#FFA726', bar: '#FFA726' },
  info:        { bg: 'rgba(33,150,243,0.10)',  border: 'rgba(33,150,243,0.22)', badge: 'rgba(33,150,243,0.18)', text: '#42a5f5', bar: '#42a5f5' },
}

function InsightCard({ scenario, delay = 0 }) {
  const s = TYPE_STYLES[scenario.type] || TYPE_STYLES.info
  const prob = scenario.prob ? parseFloat(scenario.prob) : null

  return (
    <div style={{
      background: s.bg,
      border: `1px solid ${s.border}`,
      borderRadius: 8,
      padding: '10px 12px',
      animation: `fadeUp 0.22s ease ${delay}s both`,
    }}>
      <span style={{
        display: 'inline-block',
        background: s.badge,
        color: s.text,
        fontSize: 8,
        fontWeight: 700,
        letterSpacing: 1,
        textTransform: 'uppercase',
        padding: '2px 7px',
        borderRadius: 3,
        marginBottom: 6,
      }}>
        {scenario.tag}
      </span>
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4, lineHeight: 1.3 }}>{scenario.title}</div>
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.52)', lineHeight: 1.5 }}>{scenario.body}</div>
      {prob !== null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 7 }}>
          <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${prob}%`, background: s.bar, borderRadius: 2 }} />
          </div>
          <span style={{ fontFamily: 'var(--M)', fontSize: 11, fontWeight: 700, color: s.text }}>{scenario.prob}</span>
        </div>
      )}
    </div>
  )
}

export default function DriverDrawer({ insights, onClose, driver }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (insights) {
      setVisible(false)
      const t = setTimeout(() => setVisible(true), 20)
      return () => clearTimeout(t)
    }
  }, [insights?.driver_number])

  if (!insights) return null

  const winPct   = insights.win_prob   || 0
  const podPct   = insights.podium_prob || 0
  const color    = driver?.color || '#888'
  const tireBar  = Math.round((insights.tyre_health || 0) * 100)

  return (
    <div style={{
      borderTop: `2px solid ${color}`,
      background: 'var(--c1)',
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(8px)',
      transition: 'opacity 0.25s, transform 0.25s',
    }}>
      <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}`}</style>
      <div style={{ padding: '12px 14px' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 3, height: 40, background: color, borderRadius: 2 }} />
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: 1 }}>
                {insights.full_name?.toUpperCase()}
                <span style={{ fontFamily: 'var(--M)', fontSize: 13, color: 'var(--mut)', marginLeft: 8 }}>#{insights.driver_number}</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--mut)', letterSpacing: 0.5 }}>
                P{insights.position} · {insights.team} · {driver?.tyre} tyre · {driver?.tyre_age} laps on compound
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              color: 'var(--mut)', fontSize: 18, padding: '4px 10px',
              borderRadius: 4, lineHeight: 1,
            }}
            onMouseEnter={e => { e.currentTarget.style.background='rgba(255,255,255,0.07)'; e.currentTarget.style.color='#fff' }}
            onMouseLeave={e => { e.currentTarget.style.background='transparent'; e.currentTarget.style.color='var(--mut)' }}
          >
            ✕
          </button>
        </div>

        {/* Win-O-Meter */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 14,
          background: 'var(--c3)', border: '1px solid var(--brd)', borderRadius: 8,
          padding: '10px 14px', marginBottom: 12,
        }}>
          <div>
            <div style={{ fontFamily: 'var(--M)', fontSize: 44, fontWeight: 700, lineHeight: 1, color }}>{winPct}%</div>
            <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--mut)', marginTop: 2 }}>Win chance</div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--mut)', marginBottom: 5 }}>Race win probability</div>
            <div style={{ width: '100%', height: 5, background: '#222', borderRadius: 3, overflow: 'hidden', marginBottom: 5 }}>
              <div style={{ height: '100%', width: `${winPct}%`, background: color, borderRadius: 3, transition: 'width 0.6s' }} />
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
              {winPct >= 40 ? `Strong favourite — controls the race from front.` :
               winPct >= 15 ? `Realistic contender. Strategy + tyre pace are key.` :
               winPct >= 5  ? `Outside shot. Needs rivals to make errors or have incidents.` :
               `Long odds. Requires significant chaos ahead to challenge for win.`}
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <div>
                <div style={{ fontSize: 8, color: 'var(--mut)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Podium %</div>
                <div style={{ fontFamily: 'var(--M)', fontSize: 16, fontWeight: 700 }}>{podPct}%</div>
              </div>
              <div>
                <div style={{ fontSize: 8, color: 'var(--mut)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Tyre health</div>
                <div style={{ fontFamily: 'var(--M)', fontSize: 16, fontWeight: 700, color: tireBar > 60 ? '#4caf50' : tireBar > 30 ? '#FF9800' : '#f44336' }}>{tireBar}%</div>
              </div>
            </div>
          </div>
        </div>

        {/* Scenario cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {insights.scenarios?.map((s, i) => (
            <InsightCard key={i} scenario={s} delay={i * 0.05} />
          ))}
        </div>
      </div>
    </div>
  )
}
