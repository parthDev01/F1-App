import { motion } from 'framer-motion'

export function WinProbabilityBar({ drivers = [], onSelect, selected }) {
  const top = drivers.filter(d => (d.win_probability || 0) >= 0.005)
    .sort((a, b) => (b.win_probability || 0) - (a.win_probability || 0))
  return (
    <div style={{ padding:'8px 12px' }}>
      {top.map((d, i) => {
        const pct = Math.round((d.win_probability || 0) * 100)
        return (
          <motion.div key={d.driver_code} initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }} transition={{ delay:i*0.04 }}
            onClick={() => onSelect(d.driver_code)}
            style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6, cursor:'pointer', opacity: selected && selected !== d.driver_code ? 0.5 : 1, transition:'opacity 0.2s' }}>
            <span style={{ fontFamily:"'Rajdhani', sans-serif", fontWeight:700, fontSize:12, width:30, color:d.team_color }}>{d.driver_code}</span>
            <div style={{ flex:1, height:18, background:'#1a1a1a', borderRadius:3, overflow:'hidden' }}>
              <motion.div initial={{ width:0 }} animate={{ width:`${pct}%` }} transition={{ duration:0.6, ease:'easeOut', delay:i*0.04 }}
                style={{ height:'100%', background:d.team_color, borderRadius:3, minWidth:2 }}/>
            </div>
            <span style={{ fontFamily:"'Share Tech Mono'", fontSize:11, color:'rgba(255,255,255,0.45)', width:30, textAlign:'right' }}>{pct}%</span>
          </motion.div>
        )
      })}
      <div style={{ fontSize:9, color:'rgba(255,255,255,0.15)', marginTop:4, fontFamily:"'Share Tech Mono'" }}>
        pos × pace × tyre × strategy × SC model
      </div>
    </div>
  )
}

export function IncidentGauges({ probabilities }) {
  if (!probabilities) return null
  const { safety_car=0.23, red_flag=0.08, vsc=0.15 } = probabilities
  const items = [
    { label:'Safety Car', value:safety_car, color:'#FF9800' },
    { label:'Red Flag',   value:red_flag,   color:'#f44336' },
    { label:'VSC',        value:vsc,        color:'#4CAF50' },
  ]
  return (
    <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:6, padding:'8px 12px' }}>
      {items.map(({ label, value, color }) => (
        <div key={label} style={{ background:'#1a1a1a', border:'1px solid rgba(255,255,255,0.07)', borderRadius:7, padding:'8px 10px', textAlign:'center' }}>
          <div style={{ fontSize:8, textTransform:'uppercase', letterSpacing:'1px', color:'rgba(255,255,255,0.38)', marginBottom:4 }}>{label}</div>
          <div style={{ fontFamily:"'Share Tech Mono'", fontSize:20, fontWeight:700, color }}>{Math.round(value*100)}%</div>
          <div style={{ width:'100%', height:3, background:'#2a2a2a', borderRadius:2, marginTop:5, overflow:'hidden' }}>
            <motion.div initial={{ width:0 }} animate={{ width:`${Math.round(value*100)}%` }} transition={{ duration:0.6 }}
              style={{ height:'100%', background:color, borderRadius:2 }}/>
          </div>
        </div>
      ))}
    </div>
  )
}

export function LiveStats({ drivers=[], raceState }) {
  if (!drivers.length) return null
  const fastest    = [...drivers].sort((a,b)=>(a.best_lap_time||999)-(b.best_lap_time||999))[0]
  const drsThreats = drivers.filter(d=>d.interval<1.1&&d.position>1)
  const pitWindow  = drivers.find(d=>d.tyre_age>25&&d.tyre_compound!=='HARD')
  const stats = [
    { label:'Fastest Lap', value: fastest ? `${fastest.driver_code} · ${fastest.best_lap_time?.toFixed(3)}s` : '—', accent:'#c47fe8' },
    { label:'Safety Car',  value: raceState?.safety_car ? 'DEPLOYED 🚨' : 'Clear', accent: raceState?.safety_car ? '#FF9800' : null },
    { label:'VSC',         value: raceState?.vsc ? 'ACTIVE' : 'Clear', accent: raceState?.vsc ? '#FFD700' : null },
    { label:'DRS Battles', value: drsThreats.length ? drsThreats.map(d=>`${d.driver_code}→P${d.position-1}`).join(', ') : 'None', accent: drsThreats.length ? '#4CAF50' : null },
    { label:'Pit Window',  value: pitWindow ? `${pitWindow.driver_code} overdue` : 'All clear', accent: pitWindow ? '#FF9800' : null },
    { label:'Track Temp',  value: raceState ? `${raceState.track_temp}°C` : '—', accent: null },
  ]
  return (
    <div style={{ padding:'4px 12px 8px' }}>
      {stats.map(({ label, value, accent }) => (
        <div key={label} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderBottom:'1px solid rgba(255,255,255,0.04)' }}>
          <span style={{ fontSize:9, textTransform:'uppercase', letterSpacing:'0.8px', color:'rgba(255,255,255,0.35)' }}>{label}</span>
          <span style={{ fontFamily:"'Share Tech Mono'", fontSize:11, color: accent || 'rgba(255,255,255,0.7)', fontWeight: accent ? 700 : 400 }}>{value}</span>
        </div>
      ))}
    </div>
  )
}

export function PodiumProbability({ drivers=[], onSelect }) {
  const top6 = drivers.slice(0,6)
  const medals = ['🥇','🥈','🥉','4.','5.','6.']
  return (
    <div style={{ padding:'4px 0 8px' }}>
      {top6.map((d,i) => {
        const pct = Math.round((d.podium_probability||0)*100)
        return (
          <div key={d.driver_code} onClick={()=>onSelect(d.driver_code)}
            style={{ display:'flex', alignItems:'center', gap:8, padding:'6px 12px', cursor:'pointer', borderBottom:'1px solid rgba(255,255,255,0.04)', transition:'background 0.1s' }}>
            <span style={{ fontSize:13, width:20 }}>{medals[i]}</span>
            <div style={{ width:3, height:20, background:d.team_color, borderRadius:2 }}/>
            <span style={{ fontFamily:"'Rajdhani', sans-serif", fontWeight:700, fontSize:13, flex:1 }}>{d.driver_code}</span>
            <div style={{ flex:1, height:3, background:'#1e1e1e', borderRadius:2, overflow:'hidden', margin:'0 8px' }}>
              <motion.div initial={{ width:0 }} animate={{ width:`${pct}%` }} transition={{ duration:0.5 }}
                style={{ height:'100%', background:d.team_color, borderRadius:2 }}/>
            </div>
            <span style={{ fontFamily:"'Share Tech Mono'", fontSize:11, color:d.team_color, width:30, textAlign:'right' }}>{pct}%</span>
          </div>
        )
      })}
    </div>
  )
}
