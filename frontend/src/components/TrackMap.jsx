import { useEffect, useRef, useState } from 'react'

// Bahrain track SVG path (simplified schematic)
const TRACK_PATH = "M248,188 L248,80 Q248,53 220,47 L160,47 Q131,47 117,67 Q103,87 117,107 L180,120 Q213,122 222,150 Q231,176 215,196 L126,206 Q91,206 81,184 Q71,162 95,154 L163,154 Q201,156 219,172 Q237,182 248,188"

// Per-circuit track paths — extend this map as more circuits are added
const CIRCUIT_PATHS = {
  bahrain: TRACK_PATH,
  default: TRACK_PATH,
}

// Gap (seconds) → fraction along track for demo positioning
// In production these come from OpenF1 position data directly
function gapToFraction(gap, totalLaps) {
  if (!gap || gap === 'LEADER') return 0
  const seconds = parseFloat(gap.replace('+', '')) || 0
  // approx: 1s gap ≈ 0.011 track fraction at Bahrain (92s lap)
  return Math.min(seconds * 0.011, 0.45)
}

export default function TrackMap({ drivers, circuitKey }) {
  const svgRef = useRef(null)
  const pathRef = useRef(null)
  const rafRef = useRef(null)
  const posRef = useRef({})  // driver_number → fraction along path
  const [, forceRender] = useState(0)

  const pathD = CIRCUIT_PATHS[circuitKey?.toLowerCase()] || CIRCUIT_PATHS.default

  // Initialise positions when drivers data changes
  useEffect(() => {
    if (!drivers?.length) return
    drivers.forEach(d => {
      const existingFrac = posRef.current[d.driver_number]
      if (existingFrac === undefined) {
        // Set initial position from gap
        const offset = gapToFraction(d.gap, 57)
        posRef.current[d.driver_number] = (0.55 - offset + 1) % 1
      }
    })
  }, [drivers])

  // Animation loop
  useEffect(() => {
    const speed = 1 / (92 * 0.55) // 1 track lap per ~167s at 55% animation speed

    let last = null
    function tick(ts) {
      if (last) {
        const dt = Math.min((ts - last) / 1000, 0.05)
        Object.keys(posRef.current).forEach(num => {
          posRef.current[num] = (posRef.current[num] + speed * dt) % 1
        })
        forceRender(n => n + 1)
      }
      last = ts
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [])

  function getPoint(fraction) {
    const path = pathRef.current
    if (!path) return { x: 150, y: 110 }
    try {
      const len = path.getTotalLength()
      return path.getPointAtLength(fraction * len)
    } catch {
      return { x: 150, y: 110 }
    }
  }

  const sortedDrivers = drivers ? [...drivers].sort((a, b) => b.position - a.position) : []

  return (
    <svg
      ref={svgRef}
      width="100%"
      viewBox="0 0 300 238"
      style={{ display: 'block' }}
    >
      {/* Track layers */}
      <path d={pathD} fill="none" stroke="#1c1c1c" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" />
      <path d={pathD} fill="none" stroke="#2a2a2a" strokeWidth="8"  strokeLinecap="round" strokeLinejoin="round" />

      {/* Sector overlays */}
      <path d="M248,188 L248,80 Q248,53 220,47 L160,47" fill="none" stroke="#E8002D" strokeWidth="2.5" opacity="0.4" strokeLinecap="round" />
      <path d="M160,47 Q131,47 117,67 Q103,87 117,107 L180,120 Q213,122 222,150" fill="none" stroke="#FFD700" strokeWidth="2.5" opacity="0.4" strokeLinecap="round" />
      <path d="M222,150 Q231,176 215,196 L126,206 Q91,206 81,184 Q71,162 95,154 L163,154 Q201,156 219,172 Q237,182 248,188" fill="none" stroke="#4CAF50" strokeWidth="2.5" opacity="0.4" strokeLinecap="round" />

      {/* DRS zone */}
      <line x1="248" y1="185" x2="248" y2="90" stroke="#00C853" strokeWidth="2" strokeDasharray="5 3" opacity="0.5" />
      <text x="252" y="130" fontFamily="'Share Tech Mono'" fontSize="7" fill="#00C853" opacity="0.6">DRS</text>

      {/* Start/Finish */}
      <line x1="240" y1="188" x2="256" y2="188" stroke="#fff" strokeWidth="2" opacity="0.7" />
      <text x="254" y="197" fontFamily="'Share Tech Mono'" fontSize="7" fill="rgba(255,255,255,0.35)">S/F</text>

      {/* Pit lane */}
      <path d="M243,188 L238,160" fill="none" stroke="rgba(255,200,0,0.35)" strokeWidth="1.5" strokeDasharray="3 2" />
      <text x="224" y="174" fontFamily="'Share Tech Mono'" fontSize="6" fill="rgba(255,200,0,0.4)">PIT</text>

      {/* Corner labels */}
      <text x="253" y="86" fontFamily="'Share Tech Mono'" fontSize="7" fill="rgba(255,255,255,0.22)">T1</text>
      <text x="105" y="60" fontFamily="'Share Tech Mono'" fontSize="7" fill="rgba(255,255,255,0.22)">T4</text>
      <text x="224" y="145" fontFamily="'Share Tech Mono'" fontSize="7" fill="rgba(255,255,255,0.22)">T6</text>
      <text x="62"  y="178" fontFamily="'Share Tech Mono'" fontSize="7" fill="rgba(255,255,255,0.22)">T10</text>

      {/* Circuit watermark */}
      <text x="150" y="135" fontFamily="'Rajdhani'" fontSize="9" fill="rgba(255,255,255,0.07)" textAnchor="middle" fontWeight="600" letterSpacing="3">BAHRAIN</text>

      {/* Invisible path for position calculations */}
      <path ref={pathRef} d={pathD} fill="none" stroke="none" />

      {/* Driver dots */}
      {sortedDrivers.map(d => {
        const frac = posRef.current[d.driver_number] ?? 0
        const pt = getPoint(frac)
        const isTop = d.position <= 3
        const r = isTop ? 7 : 5.5

        return (
          <g key={d.driver_number} style={{ cursor: 'pointer' }}>
            {/* Pulse ring for top 3 */}
            {isTop && (
              <circle cx={pt.x} cy={pt.y} r={r + 4} fill="none" stroke={d.color} strokeWidth="1.5" opacity="0.3" />
            )}
            <circle
              cx={pt.x} cy={pt.y} r={r}
              fill={d.color}
              stroke="rgba(0,0,0,0.7)"
              strokeWidth="1.2"
            />
            <text
              x={pt.x} y={pt.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontFamily="'Share Tech Mono'"
              fontSize={isTop ? 7 : 6}
              fontWeight="700"
              fill="#fff"
            >
              {d.position}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
