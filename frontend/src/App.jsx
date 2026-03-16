import { useEffect } from 'react'
import { useStore } from './store'
import TrackMap from './components/TrackMap'
import RaceOrder from './components/RaceOrder'
import DriverDrawer from './components/DriverDrawer'
import LapChart from './components/LapChart'
import TyreStrategy from './components/TyreStrategy'
import Standings from './components/Standings'
import {
  WinProbabilityBar, IncidentGauges, LiveStats, PodiumProbability
} from './components/WinProbability'

const SectionHeader = ({ children, right }) => (
  <div style={{
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '5px 12px',
    fontSize: 9, letterSpacing: '1.5px', textTransform: 'uppercase',
    color: 'rgba(255,255,255,0.28)',
    background: '#141414',
    borderTop: '1px solid rgba(255,255,255,0.06)',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  }}>
    <span>{children}</span>
    {right && <span style={{ fontSize: 8 }}>{right}</span>}
  </div>
)

const TABS = [
  { id: 'race',      label: 'Race'      },
  { id: 'laptimes',  label: 'Lap Times' },
  { id: 'tyres',     label: 'Tyres'     },
  { id: 'standings', label: 'Standings' },
]

export default function App() {
  const {
    raceState, connected, selectedDriver, driverInsights, loadingInsights,
    activeTab, setTab, setSelectedDriver, connectWS,
  } = useStore()

  useEffect(() => { connectWS() }, [])

  const drivers = raceState?.drivers || []
  const sorted  = [...drivers].sort((a, b) => a.position - b.position)

  const fastestCode = sorted.reduce((best, d) => {
    if (!d.best_lap_time) return best
    if (!best || d.best_lap_time < (best.best_lap_time || 999)) return d
    return best
  }, null)?.driver_code

  const selectedDriverObj = drivers.find(d => d.driver_code === selectedDriver)

  return (
    <div style={{
      background: '#0c0c0c', color: '#fff', minHeight: '100dvh',
      fontFamily: "'Rajdhani', sans-serif",
      display: 'flex', flexDirection: 'column',
      maxWidth: 900, margin: '0 auto',
    }}>

      {/* Top Bar */}
      <div style={{
        background: '#E8002D', padding: '8px 14px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
        paddingTop: 'max(8px, env(safe-area-inset-top))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontWeight: 700, fontSize: 22, letterSpacing: '3px' }}>F1</span>
          <div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.9)', letterSpacing: '0.8px', textTransform: 'uppercase', fontWeight: 600 }}>
              {raceState?.circuit_name || 'Bahrain Grand Prix'} · Rd 1
            </div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)' }}>
              {raceState?.circuit || 'Bahrain'} · {raceState?.total_laps || 57} Laps ·{' '}
              {raceState?.weather === 'wet' ? '🌧 Wet' : raceState?.weather === 'damp' ? '🌦 Damp' : '☀ Dry'} ·{' '}
              {raceState?.track_temp || 35}°C
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {raceState?.demo_mode && (
            <span style={{ fontSize: 9, background: 'rgba(0,0,0,0.25)', color: 'rgba(255,255,255,0.7)', padding: '2px 6px', borderRadius: 3 }}>
              DEMO
            </span>
          )}
          {raceState?.safety_car && (
            <span style={{ fontSize: 9, background: '#FF9800', color: '#000', fontWeight: 700, padding: '2px 7px', borderRadius: 3 }}>
              SC
            </span>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, background: '#fff', color: '#E8002D', fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 3, letterSpacing: '1px' }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: connected ? '#E8002D' : '#888', animation: connected ? 'blink 1s infinite' : 'none' }}/>
            {connected ? 'LIVE' : 'OFFLINE'}
          </div>
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>
            Lap {raceState?.current_lap || '—'}/{raceState?.total_laps || 57}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ background: '#141414', padding: '4px 12px 3px', flexShrink: 0 }}>
        <div style={{ height: 3, background: '#222', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%', background: '#E8002D', borderRadius: 2, transition: 'width 1s',
            width: `${raceState ? Math.round((raceState.current_lap / raceState.total_laps) * 100) : 47}%`,
          }}/>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2, fontSize: 9, fontFamily: "'Share Tech Mono'", color: 'rgba(255,255,255,0.25)' }}>
          <span>LAP {raceState?.current_lap || 27}</span>
          <span>{raceState ? Math.round((raceState.current_lap / raceState.total_laps) * 100) : 47}% COMPLETE</span>
          <span>{raceState?.total_laps ? `${raceState.total_laps - (raceState.current_lap || 0)} LEFT` : ''}</span>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', background: '#141414', flexShrink: 0, borderBottom: '1px solid rgba(255,255,255,0.07)', overflowX: 'auto' }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setTab(tab.id)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            padding: '10px 16px', fontSize: 12, fontWeight: 600, letterSpacing: '0.8px',
            textTransform: 'uppercase', fontFamily: "'Rajdhani', sans-serif",
            color: activeTab === tab.id ? '#E8002D' : 'rgba(255,255,255,0.38)',
            borderBottom: activeTab === tab.id ? '2px solid #E8002D' : '2px solid transparent',
            whiteSpace: 'nowrap', transition: 'color 0.15s',
          }}>{tab.label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto' }}>

        {activeTab === 'race' && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap' }}>
              {/* Left: Track + Order */}
              <div style={{ flex: '1 1 300px', borderRight: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column' }}>
                <SectionHeader right={<span style={{ color: '#4CAF50' }}>● GPS 3Hz</span>}>Live Track Position</SectionHeader>
                <TrackMap drivers={sorted} selected={selectedDriver} onSelectDriver={setSelectedDriver}/>
                <SectionHeader right="TAP ROW FOR INSIGHTS">Race Order</SectionHeader>
                <RaceOrder drivers={sorted} selected={selectedDriver} onSelect={setSelectedDriver} fastestLapCode={fastestCode}/>
              </div>
              {/* Right: Probabilities */}
              <div style={{ flex: '1 1 260px', display: 'flex', flexDirection: 'column', overflowY: 'auto', maxHeight: '80vh' }}>
                <SectionHeader>Race Win Probability</SectionHeader>
                <WinProbabilityBar drivers={sorted} selected={selectedDriver} onSelect={setSelectedDriver}/>
                <SectionHeader>Incident Probability</SectionHeader>
                <IncidentGauges probabilities={raceState?.incident_probability}/>
                <SectionHeader>Live Stats</SectionHeader>
                <LiveStats drivers={sorted} raceState={raceState}/>
                <SectionHeader>Podium Probability</SectionHeader>
                <PodiumProbability drivers={sorted} onSelect={setSelectedDriver}/>
              </div>
            </div>
            {/* Drawer: full width below columns */}
            <DriverDrawer
              driver={selectedDriverObj}
              insights={driverInsights}
              loading={loadingInsights}
              onClose={() => setSelectedDriver(selectedDriver)}
            />
          </div>
        )}

        {activeTab === 'laptimes' && (
          <><SectionHeader>Lap Time Chart</SectionHeader><LapChart drivers={sorted}/></>
        )}

        {activeTab === 'tyres' && (
          <><SectionHeader>Tyre Strategy</SectionHeader><TyreStrategy drivers={sorted} currentLap={raceState?.current_lap || 27}/></>
        )}

        {activeTab === 'standings' && <Standings/>}
      </div>

      <div style={{ height: 'env(safe-area-inset-bottom)', background: '#0c0c0c', flexShrink: 0 }}/>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.15} }
        * { -webkit-tap-highlight-color: transparent; box-sizing: border-box; }
        ::-webkit-scrollbar { width: 3px; height: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 2px; }
      `}</style>
    </div>
  )
}
