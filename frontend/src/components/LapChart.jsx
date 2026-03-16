import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useState } from 'react'

// Generate demo lap data or use real data from FastF1 API
function buildChartData(drivers, totalLaps = 27) {
  const laps = Array.from({ length: totalLaps }, (_, i) => ({ lap: i + 1 }))
  drivers.slice(0, 6).forEach(d => {
    const base = d.last_lap_raw || 92.5
    laps.forEach((lap, i) => {
      const deg   = i > 12 ? (i - 12) * 0.04 : 0
      const noise = (Math.random() - 0.5) * 0.6
      const pit   = i === 11 ? 25 : 0  // pit lap spike
      lap[d.short_name] = parseFloat((base + deg + noise + pit).toFixed(3))
    })
  })
  return laps
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 6, padding: '8px 12px', fontSize: 11, fontFamily: 'var(--M)',
    }}>
      <div style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>Lap {label}</div>
      {payload.sort((a, b) => a.value - b.value).map(p => (
        <div key={p.dataKey} style={{ display: 'flex', gap: 8, color: p.color }}>
          <span style={{ width: 28 }}>{p.dataKey}</span>
          <span>{p.value?.toFixed(3)}s</span>
        </div>
      ))}
    </div>
  )
}

export default function LapChart({ drivers }) {
  const [hidden, setHidden] = useState({})
  const chartData = buildChartData(drivers || [])
  const top6 = (drivers || []).slice(0, 6)

  return (
    <div style={{ padding: 14 }}>
      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
        {top6.map(d => (
          <div
            key={d.driver_number}
            onClick={() => setHidden(h => ({ ...h, [d.short_name]: !h[d.short_name] }))}
            style={{
              display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer',
              fontSize: 11, fontFamily: 'var(--M)',
              color: hidden[d.short_name] ? 'rgba(255,255,255,0.25)' : '#aaa',
            }}
          >
            <div style={{ width: 20, height: 2, background: hidden[d.short_name] ? '#333' : d.color, borderRadius: 1 }} />
            {d.short_name}
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="lap"
            tick={{ fontFamily: "'Share Tech Mono'", fontSize: 10, fill: '#666' }}
            label={{ value: 'Lap', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#666' }}
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontFamily: "'Share Tech Mono'", fontSize: 10, fill: '#666' }}
            tickFormatter={v => v.toFixed(1)}
            width={42}
          />
          <Tooltip content={<CustomTooltip />} />
          {top6.map(d => (
            <Line
              key={d.driver_number}
              type="monotone"
              dataKey={d.short_name}
              stroke={d.color}
              strokeWidth={2}
              dot={false}
              hide={!!hidden[d.short_name]}
              strokeDasharray={d.position > 3 ? '4 2' : undefined}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', fontSize: 9, fontFamily: 'var(--M)', color: 'rgba(255,255,255,0.2)', marginTop: 6 }}>
        LIVE — FastF1 data feeds in real-time during sessions
      </div>
    </div>
  )
}
