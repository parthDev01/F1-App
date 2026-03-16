import { motion } from 'framer-motion'

const TYRE_STYLE = {
  SOFT:   { bg: '#E8002D', color: '#fff' },
  MEDIUM: { bg: '#FFD700', color: '#000' },
  HARD:   { bg: '#c8c8c8', color: '#000' },
  INTER:  { bg: '#39B54A', color: '#fff' },
  WET:    { bg: '#0067FF', color: '#fff' },
}

function formatGap(gap) {
  if (!gap || gap === 0) return 'LEADER'
  if (typeof gap === 'string') return gap
  return `+${gap.toFixed(3)}`
}

function formatLapTime(t) {
  if (!t) return '—'
  const mins = Math.floor(t / 60)
  const secs = (t % 60).toFixed(3).padStart(6, '0')
  return `${mins}:${secs}`
}

export default function RaceOrder({ drivers = [], selected, onSelect, fastestLapCode }) {
  return (
    <div style={{ flex: 1, overflowY: 'auto' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '24px 12px 48px 1fr 80px 58px 60px',
        gap: 5, padding: '4px 10px 6px',
        fontSize: 9, letterSpacing: '1.2px', textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.25)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <span>P</span><span></span><span></span>
        <span>Driver</span>
        <span style={{ textAlign: 'right' }}>Gap</span>
        <span>Tyre</span>
        <span style={{ textAlign: 'right' }}>Last Lap</span>
      </div>
      {drivers.map((d, i) => {
        const isSel  = selected === d.driver_code
        const tyre   = TYRE_STYLE[d.tyre_compound] || TYRE_STYLE.MEDIUM
        const isFast = d.driver_code === fastestLapCode
        return (
          <motion.div
            key={d.driver_code}
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
            onClick={() => onSelect(d.driver_code)}
            style={{
              display: 'grid',
              gridTemplateColumns: '24px 12px 48px 1fr 80px 58px 60px',
              gap: 5, alignItems: 'center',
              padding: '6px 10px', cursor: 'pointer',
              background: isSel ? 'rgba(232,0,45,0.08)' : 'transparent',
              borderLeft: isSel ? `2px solid ${d.team_color}` : '2px solid transparent',
              borderBottom: '1px solid rgba(255,255,255,0.04)',
              transition: 'background 0.12s',
            }}
          >
            <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, fontWeight: 700, textAlign: 'center' }}>
              {d.position}
            </span>
            <div style={{ width: 3, height: 28, background: d.team_color, borderRadius: 2 }}/>
            <div>
              <div style={{ fontFamily: "'Rajdhani', sans-serif", fontWeight: 700, fontSize: 13 }}>{d.driver_code}</div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.35)' }}>{d.team?.split(' ')[0]}</div>
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.65)', fontFamily: "'Rajdhani', sans-serif", fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {d.full_name?.split(' ').pop()}
              </div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.25)' }}>#{d.driver_number}</div>
            </div>
            <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 11, color: d.position === 1 ? 'rgba(255,255,255,0.5)' : '#FFD700', textAlign: 'right' }}>
              {formatGap(d.gap_to_leader)}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <div style={{ width: 15, height: 15, borderRadius: '50%', background: tyre.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 8, fontWeight: 700, color: tyre.color }}>
                {d.tyre_compound?.[0]}
              </div>
              <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>{d.tyre_age}L</span>
            </div>
            <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, textAlign: 'right', color: isFast ? '#c47fe8' : 'rgba(255,255,255,0.45)' }}>
              {formatLapTime(d.last_lap_time)}{isFast ? ' ⚡' : ''}
            </span>
          </motion.div>
        )
      })}
    </div>
  )
}
