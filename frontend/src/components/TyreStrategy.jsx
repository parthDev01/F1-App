import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const COMPOUND_COLORS = { SOFT:'#E8002D', MEDIUM:'#FFD700', HARD:'#c8c8c8', INTER:'#39B54A', WET:'#0067FF', UNKNOWN:'#888' }

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background:'#1a1a1a', border:'1px solid rgba(255,255,255,0.1)', borderRadius:7, padding:'8px 12px', fontSize:11, fontFamily:"'Share Tech Mono'" }}>
      <div style={{ fontWeight:700, marginBottom:4, fontFamily:"'Rajdhani'" }}>{label}</div>
      {payload.map(p => p.value > 0 && (
        <div key={p.name} style={{ color: COMPOUND_COLORS[p.name] || '#888' }}>{p.name}: {p.value} laps</div>
      ))}
    </div>
  )
}

export default function TyreStrategy({ drivers = [], currentLap = 27 }) {
  const compounds = ['SOFT', 'MEDIUM', 'HARD', 'INTER', 'WET']
  const chartData = drivers.map(d => {
    const row = { driver: d.driver_code }
    if (d.pit_stops === 0) {
      row[d.tyre_compound] = currentLap
    } else {
      const prev = d.tyre_compound === 'SOFT' ? 'MEDIUM' : 'SOFT'
      const split = Math.round(currentLap * 0.48)
      row[prev] = split
      row[d.tyre_compound] = currentLap - split
    }
    return row
  })
  return (
    <div style={{ padding: '12px 14px' }}>
      <div style={{ display:'flex', gap:12, marginBottom:12, flexWrap:'wrap' }}>
        {compounds.map(c => (
          <div key={c} style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, color:'rgba(255,255,255,0.5)' }}>
            <div style={{ width:10, height:10, borderRadius:2, background:COMPOUND_COLORS[c] }}/>{c[0]+c.slice(1).toLowerCase()}
          </div>
        ))}
      </div>
      <div style={{ height: Math.max(280, drivers.length * 36 + 60) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top:5, right:15, left:10, bottom:20 }} barCategoryGap="20%">
            <XAxis type="number" tick={{ fill:'rgba(255,255,255,0.35)', fontSize:10, fontFamily:"'Share Tech Mono'" }} axisLine={{ stroke:'rgba(255,255,255,0.1)' }} tickLine={false}
              label={{ value:'Laps', position:'insideBottom', offset:-10, fill:'rgba(255,255,255,0.2)', fontSize:10 }}/>
            <YAxis dataKey="driver" type="category" tick={{ fill:'#fff', fontSize:12, fontWeight:700, fontFamily:"'Rajdhani'" }} axisLine={false} tickLine={false} width={36}/>
            <Tooltip content={<CustomTooltip/>} cursor={{ fill:'rgba(255,255,255,0.03)' }}/>
            {compounds.map(c => <Bar key={c} dataKey={c} stackId="a" fill={COMPOUND_COLORS[c]} fillOpacity={0.9} radius={[0,2,2,0]}/>)}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ textAlign:'center', fontSize:10, color:'rgba(255,255,255,0.2)', fontFamily:"'Share Tech Mono'", marginTop:4 }}>
        Lap {currentLap} · Full history from FastF1 after session ends
      </div>
    </div>
  )
}
