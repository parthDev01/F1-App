import { motion } from 'framer-motion'

// 2025 WDC standings (static — live version would come from Ergast/Jolpica API)
const STANDINGS_DATA = [
  { pos:1,  driver:'Max Verstappen',    code:'VER', team:'Red Bull Racing', color:'#3671C6', pts:412, wins:19, podiums:22 },
  { pos:2,  driver:'Lando Norris',      code:'NOR', team:'McLaren',         color:'#FF8000', pts:374, wins:6,  podiums:14 },
  { pos:3,  driver:'Charles Leclerc',   code:'LEC', team:'Ferrari',         color:'#E8002D', pts:356, wins:3,  podiums:11 },
  { pos:4,  driver:'Oscar Piastri',     code:'PIA', team:'McLaren',         color:'#FF8000', pts:292, wins:2,  podiums:9  },
  { pos:5,  driver:'Carlos Sainz',      code:'SAI', team:'Ferrari',         color:'#E8002D', pts:290, wins:2,  podiums:8  },
  { pos:6,  driver:'Lewis Hamilton',    code:'HAM', team:'Mercedes',        color:'#27F4D2', pts:211, wins:0,  podiums:5  },
  { pos:7,  driver:'George Russell',    code:'RUS', team:'Mercedes',        color:'#27F4D2', pts:202, wins:1,  podiums:6  },
  { pos:8,  driver:'Sergio Perez',      code:'PER', team:'Red Bull Racing', color:'#3671C6', pts:152, wins:0,  podiums:2  },
  { pos:9,  driver:'Fernando Alonso',   code:'ALO', team:'Aston Martin',    color:'#358C75', pts:68,  wins:0,  podiums:0  },
  { pos:10, driver:'Lance Stroll',      code:'STR', team:'Aston Martin',    color:'#358C75', pts:24,  wins:0,  podiums:0  },
  { pos:11, driver:'Pierre Gasly',      code:'GAS', team:'Alpine',          color:'#0093CC', pts:22,  wins:0,  podiums:0  },
  { pos:12, driver:'Nico Hulkenberg',   code:'HUL', team:'Haas',            color:'#B6BABD', pts:18,  wins:0,  podiums:0  },
  { pos:13, driver:'Yuki Tsunoda',      code:'TSU', team:'RB',              color:'#5E8FAA', pts:17,  wins:0,  podiums:0  },
  { pos:14, driver:'Valtteri Bottas',   code:'BOT', team:'Kick Sauber',     color:'#52E252', pts:9,   wins:0,  podiums:0  },
  { pos:15, driver:'Esteban Ocon',      code:'OCO', team:'Alpine',          color:'#0093CC', pts:8,   wins:0,  podiums:0  },
  { pos:16, driver:'Kevin Magnussen',   code:'MAG', team:'Haas',            color:'#B6BABD', pts:4,   wins:0,  podiums:0  },
  { pos:17, driver:'Alexander Albon',   code:'ALB', team:'Williams',        color:'#005AFF', pts:4,   wins:0,  podiums:0  },
  { pos:18, driver:'Guanyu Zhou',       code:'ZHO', team:'Kick Sauber',     color:'#52E252', pts:2,   wins:0,  podiums:0  },
  { pos:19, driver:'Logan Sargeant',    code:'SAR', team:'Williams',        color:'#005AFF', pts:1,   wins:0,  podiums:0  },
  { pos:20, driver:'Daniel Ricciardo',  code:'RIC', team:'RB',              color:'#5E8FAA', pts:0,   wins:0,  podiums:0  },
]

const CONSTRUCTOR_STANDINGS = [
  { pos:1, team:'Red Bull Racing', color:'#3671C6', pts:564 },
  { pos:2, team:'Ferrari',         color:'#E8002D', pts:646 },
  { pos:3, team:'McLaren',         color:'#FF8000', pts:666 },
  { pos:4, team:'Mercedes',        color:'#27F4D2', pts:413 },
  { pos:5, team:'Aston Martin',    color:'#358C75', pts:92  },
  { pos:6, team:'Alpine',          color:'#0093CC', pts:30  },
  { pos:7, team:'Haas',            color:'#B6BABD', pts:22  },
  { pos:8, team:'RB',              color:'#5E8FAA', pts:17  },
  { pos:9, team:'Williams',        color:'#005AFF', pts:5   },
  { pos:10,team:'Kick Sauber',     color:'#52E252', pts:11  },
]

const MAX_PTS = 566

export default function Standings() {
  return (
    <div style={{ padding: '0 0 40px' }}>

      {/* WDC */}
      <div style={{
        fontSize: 9, letterSpacing: '1.5px', textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.28)', padding: '6px 12px',
        background: '#141414', borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        Drivers Championship
      </div>

      {STANDINGS_DATA.map((d, i) => (
        <motion.div
          key={d.code}
          initial={{ opacity: 0, x: -6 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.025 }}
          style={{
            display: 'grid',
            gridTemplateColumns: '28px 3px 1fr 60px 40px',
            alignItems: 'center', gap: 8,
            padding: '9px 12px',
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            cursor: 'default',
          }}
        >
          {/* Position */}
          <span style={{
            fontFamily: "'Share Tech Mono'", fontSize: 15, fontWeight: 700,
            color: d.pos <= 3 ? ['#FFD700','#C0C0C0','#CD7F32'][d.pos-1] : 'rgba(255,255,255,0.5)',
            textAlign: 'center',
          }}>
            {d.pos}
          </span>

          {/* Team color bar */}
          <div style={{ width: 3, height: 32, background: d.color, borderRadius: 2 }}/>

          {/* Driver info + bar */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 14, fontFamily: "'Rajdhani', sans-serif" }}>{d.driver}</span>
                <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginLeft: 6 }}>{d.team}</span>
              </div>
              <div style={{ display: 'flex', gap: 6, fontSize: 9, color: 'rgba(255,255,255,0.3)', fontFamily: "'Share Tech Mono'" }}>
                {d.wins > 0 && <span style={{ color: '#FFD700' }}>{d.wins}W</span>}
                {d.podiums > 0 && <span>{d.podiums}P</span>}
              </div>
            </div>
            {/* Points bar */}
            <div style={{ height: 3, background: '#1e1e1e', borderRadius: 2, overflow: 'hidden' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(d.pts / MAX_PTS) * 100}%` }}
                transition={{ duration: 0.6, delay: i * 0.025 }}
                style={{ height: '100%', background: d.color, borderRadius: 2, opacity: 0.75 }}
              />
            </div>
          </div>

          {/* Points */}
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, color: '#FFD700', textAlign: 'right', fontWeight: 700 }}>
            {d.pts}
          </span>

          {/* Gap to leader */}
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'rgba(255,255,255,0.25)', textAlign: 'right' }}>
            {d.pos === 1 ? '' : `−${STANDINGS_DATA[0].pts - d.pts}`}
          </span>
        </motion.div>
      ))}

      {/* WCC */}
      <div style={{
        fontSize: 9, letterSpacing: '1.5px', textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.28)', padding: '6px 12px',
        background: '#141414',
        borderTop: '1px solid rgba(255,255,255,0.08)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        marginTop: 12,
      }}>
        Constructors Championship
      </div>

      {CONSTRUCTOR_STANDINGS.map((c, i) => {
        const maxC = CONSTRUCTOR_STANDINGS[0].pts
        return (
          <motion.div
            key={c.team}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 + 0.3 }}
            style={{
              display: 'grid',
              gridTemplateColumns: '28px 3px 1fr 55px',
              alignItems: 'center', gap: 8,
              padding: '8px 12px',
              borderBottom: '1px solid rgba(255,255,255,0.04)',
            }}
          >
            <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 15, fontWeight: 700, textAlign: 'center', color: 'rgba(255,255,255,0.5)' }}>
              {c.pos}
            </span>
            <div style={{ width: 3, height: 28, background: c.color, borderRadius: 2 }}/>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, fontFamily: "'Rajdhani', sans-serif", marginBottom: 4 }}>{c.team}</div>
              <div style={{ height: 3, background: '#1e1e1e', borderRadius: 2, overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(c.pts / maxC) * 100}%` }}
                  transition={{ duration: 0.6, delay: i * 0.03 + 0.3 }}
                  style={{ height: '100%', background: c.color, borderRadius: 2, opacity: 0.75 }}
                />
              </div>
            </div>
            <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, color: '#FFD700', textAlign: 'right' }}>
              {c.pts}
            </span>
          </motion.div>
        )
      })}
    </div>
  )
}
