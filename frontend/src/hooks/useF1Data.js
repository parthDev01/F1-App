import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''
const WS_BASE  = import.meta.env.VITE_WS_URL  || ''

// Demo/mock data so the UI works without a live race session
const MOCK_STATE = {
  session_name: 'Race',
  meeting_name: '2025 Bahrain Grand Prix',
  location: 'Sakhir',
  total_laps: 57,
  current_lap: 27,
  weather: { air_temp: 29, track_temp: 43, humidity: 42, rainfall: 0 },
  drivers: [
    { driver_number:'1',  position:1,  short_name:'VER', full_name:'Max Verstappen',    team:'Red Bull Racing', color:'#3671C6', gap:'LEADER',  tyre:'M', tyre_age:12, last_lap:'1:32.456', last_lap_raw:92.456, pit_stops:1, speed:320, throttle:88, brake:0, gear:8, rpm:11800, drs:true,  sector1:28.2, sector2:32.1, sector3:32.1 },
    { driver_number:'44', position:2,  short_name:'HAM', full_name:'Lewis Hamilton',     team:'Mercedes',       color:'#27F4D2', gap:'+4.234',  tyre:'M', tyre_age:12, last_lap:'1:32.891', last_lap_raw:92.891, pit_stops:1, speed:318, throttle:85, brake:0, gear:8, rpm:11650, drs:true,  sector1:28.4, sector2:32.3, sector3:32.1 },
    { driver_number:'16', position:3,  short_name:'LEC', full_name:'Charles Leclerc',    team:'Ferrari',        color:'#E8002D', gap:'+7.109',  tyre:'S', tyre_age:6,  last_lap:'1:32.711', last_lap_raw:92.711, pit_stops:1, speed:315, throttle:92, brake:5, gear:7, rpm:11900, drs:false, sector1:28.1, sector2:32.0, sector3:32.6, is_fastest_lap:true },
    { driver_number:'11', position:4,  short_name:'PER', full_name:'Sergio Perez',       team:'Red Bull Racing', color:'#3671C6', gap:'+12.44', tyre:'M', tyre_age:15, last_lap:'1:33.201', last_lap_raw:93.201, pit_stops:1, speed:312, throttle:80, brake:2, gear:8, rpm:11500, drs:false, sector1:28.6, sector2:32.4, sector3:32.2 },
    { driver_number:'55', position:5,  short_name:'SAI', full_name:'Carlos Sainz',       team:'Ferrari',        color:'#E8002D', gap:'+15.88', tyre:'H', tyre_age:22, last_lap:'1:33.544', last_lap_raw:93.544, pit_stops:1, speed:310, throttle:78, brake:0, gear:8, rpm:11400, drs:false, sector1:28.8, sector2:32.5, sector3:32.2 },
    { driver_number:'63', position:6,  short_name:'RUS', full_name:'George Russell',     team:'Mercedes',       color:'#27F4D2', gap:'+19.23', tyre:'H', tyre_age:22, last_lap:'1:33.788', last_lap_raw:93.788, pit_stops:1, speed:309, throttle:76, brake:0, gear:8, rpm:11350, drs:true,  sector1:28.9, sector2:32.6, sector3:32.2 },
    { driver_number:'4',  position:7,  short_name:'NOR', full_name:'Lando Norris',       team:'McLaren',        color:'#FF8000', gap:'+23.11', tyre:'M', tyre_age:8,  last_lap:'1:34.012', last_lap_raw:94.012, pit_stops:1, speed:307, throttle:82, brake:3, gear:7, rpm:11300, drs:false, sector1:29.0, sector2:32.7, sector3:32.3 },
    { driver_number:'81', position:8,  short_name:'PIA', full_name:'Oscar Piastri',      team:'McLaren',        color:'#FF8000', gap:'+27.67', tyre:'M', tyre_age:8,  last_lap:'1:34.234', last_lap_raw:94.234, pit_stops:1, speed:305, throttle:79, brake:0, gear:8, rpm:11250, drs:false, sector1:29.1, sector2:32.8, sector3:32.3 },
    { driver_number:'14', position:9,  short_name:'ALO', full_name:'Fernando Alonso',    team:'Aston Martin',   color:'#358C75', gap:'+31.99', tyre:'H', tyre_age:18, last_lap:'1:34.456', last_lap_raw:94.456, pit_stops:1, speed:304, throttle:75, brake:0, gear:8, rpm:11200, drs:true,  sector1:29.2, sector2:32.9, sector3:32.3 },
    { driver_number:'18', position:10, short_name:'STR', full_name:'Lance Stroll',       team:'Aston Martin',   color:'#358C75', gap:'+38.22', tyre:'H', tyre_age:18, last_lap:'1:34.788', last_lap_raw:94.788, pit_stops:1, speed:302, throttle:72, brake:0, gear:8, rpm:11100, drs:false, sector1:29.3, sector2:33.0, sector3:32.4 },
  ],
  probabilities: {
    win:  { '1':52, '44':18, '16':15, '11':7, '55':4, '63':2, '4':1, '81':0.5, '14':0.3, '18':0.2 },
    podium: { '1':94, '44':76, '16':64, '11':28, '55':15, '63':10, '4':6, '81':3, '14':2, '18':1 },
    sc_prob:23, rf_prob:8, vsc_prob:15,
    fl_candidates: ['LEC','VER','HAM'],
    pit_windows: { '44':'30-34', '11':'28-31', '63':'31-35' },
  },
}

const MOCK_INSIGHTS = {
  '16': {
    driver_number:'16', short_name:'LEC', full_name:'Charles Leclerc', team:'Ferrari',
    position:3, win_prob:15, podium_prob:64, tyre_health:0.88, laps_to_cliff:14,
    scenarios:[
      { tag:'OPPORTUNITY', type:'opportunity', title:"HAM tyre cliff in 5–6 laps", body:"Hamilton's 12-lap mediums hit degradation soon. LEC on fresh softs gains 0.3s/lap — gap closes to DRS range by Lap 33.", prob:'41%' },
      { tag:'SCENARIO',    type:'opportunity', title:'T6 lock-up → P2 in ~3 laps', body:"If HAM locks up at Turn 6 (peak tyre stress braking zone), LEC gains 0.8s instantly and enters DRS range in ~3 laps.", prob:'22%' },
      { tag:'PIT WINDOW',  type:'warning',     title:'Optimal stop: Laps 31–35',    body:'Ferrari pits 1–2 laps ahead of HAM. On hard tyre with clean air, LEC exits P2 with a 2.1s margin and controls to the finish.', prob:'35%' },
      { tag:'WIN PATH',    type:'risk',        title:'P1 requires VER incident',    body:"LEC reaching P1 needs VER DNF + clean execution. Combined probability ~8%. Realistic ceiling today: P2.", prob:'8%' },
    ],
  },
}

export function useF1Data() {
  const [state, setState]       = useState(null)
  const [loading, setLoading]   = useState(true)
  const [connected, setConnected] = useState(false)
  const [useMock, setUseMock]   = useState(false)
  const wsRef = useRef(null)
  const retryRef = useRef(null)

  const fetchREST = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/live`)
      if (!r.ok) throw new Error('no session')
      const data = await r.json()
      if (data.error) throw new Error(data.error)
      setState(data)
      setUseMock(false)
    } catch {
      setState(MOCK_STATE)
      setUseMock(true)
    } finally {
      setLoading(false)
    }
  }, [])

  const connectWS = useCallback(() => {
    const wsUrl = WS_BASE
      ? `${WS_BASE}/ws/live`
      : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/live`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        clearTimeout(retryRef.current)
      }

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'live_update' && msg.data) {
            setState(msg.data)
            setUseMock(false)
            setLoading(false)
          }
        } catch {}
      }

      ws.onclose = () => {
        setConnected(false)
        retryRef.current = setTimeout(connectWS, 5000)
      }

      ws.onerror = () => {
        ws.close()
        fetchREST() // fall back to REST poll
      }
    } catch {
      fetchREST()
    }
  }, [fetchREST])

  useEffect(() => {
    fetchREST()
    connectWS()
    const poll = setInterval(fetchREST, 8000)
    return () => {
      clearInterval(poll)
      clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [fetchREST, connectWS])

  const fetchInsights = useCallback(async (driverNumber) => {
    // Return mock if no backend
    if (useMock) {
      return MOCK_INSIGHTS[driverNumber] || generateMockInsight(driverNumber, state)
    }
    try {
      const r = await fetch(`${API_BASE}/api/driver/${driverNumber}/insights`)
      return await r.json()
    } catch {
      return generateMockInsight(driverNumber, state)
    }
  }, [useMock, state])

  return { state, loading, connected, useMock, fetchInsights }
}

function generateMockInsight(driverNumber, state) {
  const driver = state?.drivers?.find(d => d.driver_number === driverNumber)
  if (!driver) return null
  const winProb = state?.probabilities?.win?.[driverNumber] || 1
  return {
    driver_number: driverNumber,
    short_name: driver.short_name,
    full_name: driver.full_name,
    team: driver.team,
    position: driver.position,
    win_prob: winProb,
    podium_prob: state?.probabilities?.podium?.[driverNumber] || 5,
    tyre_health: 0.7,
    laps_to_cliff: 10,
    scenarios: [
      { tag:'STATUS',    type:'info',        title:`P${driver.position} — tracking pace`, body:`${driver.short_name} on ${driver.tyre} tyres (${driver.tyre_age} laps). Holding current position cleanly.`, prob:null },
      { tag:'SC FACTOR', type:'opportunity', title:'Safety car reshuffles the grid',       body:`23% SC probability. Any neutralisation compresses gaps and creates a restart sprint.`, prob:'23%' },
      { tag:'TYRE',      type:'warning',     title:`${driver.tyre} compound window`,        body:`At ${driver.tyre_age} laps, approaching the ${driver.tyre==='S'?'20':driver.tyre==='M'?'32':'45'}-lap optimal window. Monitor closely.`, prob:null },
      { tag:'WIN PATH',  type:'risk',        title:`${winProb}% race win probability`,     body:`From P${driver.position}, win requires significant pace gain or chaos ahead. Focus on maximising points.`, prob:`${winProb}%` },
    ],
  }
}
