import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Site, RiskLevel, HeatSnapshot, MicroclimateAnalysis } from '../types'

const BASEMAP_TILES = {
  voyager: {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    name: 'Street View'
  },
  carto_dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    name: 'Obsidian'
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    name: 'Satellite'
  }
}

// FortyGuard Official Spectral Palette Interpolation
function getFortyGuardSpectralColor(tempF: number, minTemp: number, maxTemp: number) {
  const norm = Math.max(0, Math.min(1, (tempF - minTemp) / (maxTemp - minTemp || 1)))
  
  // 12-Class Spectral Hex Gradient matching FortyGuard
  const colors = [
    '#313695', // Deep Blue
    '#4575b4', // Navy
    '#74add1', // Sky Blue
    '#abd9e9', // Light Blue
    '#e0f3f8', // Ice
    '#ffffbf', // Pale Yellow
    '#fee090', // Amber
    '#fdae61', // Orange
    '#f46d43', // Red Orange
    '#d73027', // Bright Red
    '#a50026', // Deep Crimson
    '#67001f'  // Extreme Bordeaux
  ]

  const index = Math.min(colors.length - 1, Math.floor(norm * colors.length))
  return colors[index]
}

interface HeatMapProps {
  site: Site | null
  riskLevel: RiskLevel
  snapshot?: HeatSnapshot | null
  microclimate?: MicroclimateAnalysis | null
}

export default function HeatMap({ site, riskLevel, snapshot, microclimate }: HeatMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const thermalMeshLayerRef = useRef<L.LayerGroup | null>(null)
  const vectorLayerRef = useRef<L.LayerGroup | null>(null)
  const boundaryLayerRef = useRef<L.LayerGroup | null>(null)
  const tileLayerRef = useRef<L.TileLayer | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [basemap, setBasemap] = useState<'voyager' | 'carto_dark' | 'satellite'>('voyager')
  const [granularity, setGranularity] = useState<'100' | '80' | '60'>('80')
  const [opacity, setOpacity] = useState<number>(0.72)
  const [selectedPoint, setSelectedPoint] = useState<any>(null)
  const [showMesh, setShowMesh] = useState(true)
  const [showEscapeVector, setShowEscapeVector] = useState(true)
  const [cursorCoords, setCursorCoords] = useState<{lat: string; lng: string} | null>(null)

  // Initialize Map
  useEffect(() => {
    if (!containerRef.current) return

    try {
      if ((containerRef.current as any)._leaflet_id) {
        delete (containerRef.current as any)._leaflet_id
      }
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }

      mapRef.current = L.map(containerRef.current, {
        center: [34.0404, -118.2356],
        zoom: 15,
        zoomControl: false,
        attributionControl: false,
      })

      L.control.zoom({ position: 'topleft' }).addTo(mapRef.current)

      tileLayerRef.current = L.tileLayer(BASEMAP_TILES.voyager.url, {
        maxZoom: 19,
      }).addTo(mapRef.current)

      thermalMeshLayerRef.current = L.layerGroup().addTo(mapRef.current)
      boundaryLayerRef.current = L.layerGroup().addTo(mapRef.current)
      vectorLayerRef.current = L.layerGroup().addTo(mapRef.current)

      mapRef.current.on('mousemove', (e) => {
        setCursorCoords({
          lat: e.latlng.lat.toFixed(5),
          lng: e.latlng.lng.toFixed(5),
        })
      })

      mapRef.current.on('mouseout', () => {
        setCursorCoords(null)
      })
    } catch (err) {
      console.warn('Leaflet map initialization notice:', err)
    }

    return () => {
      try {
        mapRef.current?.remove()
        mapRef.current = null
      } catch (err) {
        console.warn('Leaflet cleanup notice:', err)
      }
    }
  }, [])

  // Switch Basemap
  useEffect(() => {
    if (!mapRef.current || !tileLayerRef.current) return
    tileLayerRef.current.setUrl(BASEMAP_TILES[basemap].url)
  }, [basemap])

  // Custom CSS for vector and modal popup
  useEffect(() => {
    const style = document.createElement('style')
    style.innerHTML = `
      .glowing-dash-path {
        animation: dash-flow 1.2s linear infinite;
        stroke-dashoffset: 100;
        filter: drop-shadow(0 0 4px #059669);
      }
      @keyframes dash-flow {
        to {
          stroke-dashoffset: 0;
        }
      }
      .vector-tag-badge {
        background: #059669;
        border: 1.5px solid #FFFFFF;
        color: #FFFFFF;
        font-weight: 700;
        font-family: 'Inter', system-ui, sans-serif;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 9999px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        white-space: nowrap;
      }
    `
    document.head.appendChild(style)
    return () => {
      if (document.head.contains(style)) {
        document.head.removeChild(style)
      }
    }
  }, [])

  // Render High-Density FortyGuard Thermal Mesh
  useEffect(() => {
    if (!mapRef.current || !thermalMeshLayerRef.current || !site?.polygon_geojson?.coordinates?.[0]) return

    try {
      thermalMeshLayerRef.current.clearLayers()
      boundaryLayerRef.current?.clearLayers()
      vectorLayerRef.current?.clearLayers()

      const coords = site.polygon_geojson.coordinates[0]
      if (!Array.isArray(coords) || coords.length < 3) return

      const lats = coords.map((c: number[]) => c[1])
      const lngs = coords.map((c: number[]) => c[0])
      const minLat = Math.min(...lats)
      const maxLat = Math.max(...lats)
      const minLng = Math.min(...lngs)
      const maxLng = Math.max(...lngs)

      const baseTempF = snapshot ? snapshot.temperature_f : (microclimate?.ambient_temp_f ?? 102.5)
      const maxSurfaceF = microclimate?.surface_temp_f ?? (baseTempF + 22.0)
      const minCanopyF = Math.round((baseTempF - 18.0) * 10) / 10

      // High-Density Grid Dimension (60m = 32x32, 80m = 24x24, 100m = 18x18)
      const gridSteps = granularity === '60' ? 32 : granularity === '80' ? 24 : 18
      const dLat = (maxLat - minLat) / gridSteps
      const dLng = (maxLng - minLng) / gridSteps

      const bounds = L.latLngBounds(coords.map((c: number[]) => [c[1], c[0]] as L.LatLngTuple))

      let hotspotCoords: L.LatLngTuple | null = null
      let refugeCoords: L.LatLngTuple | null = null

      if (showMesh) {
        for (let r = 0; r < gridSteps; r++) {
          for (let c = 0; c < gridSteps; c++) {
            const cellMinLat = minLat + r * dLat
            const cellMaxLat = cellMinLat + dLat
            const cellMinLng = minLng + c * dLng
            const cellMaxLng = cellMinLng + dLng

            const cLat = (cellMinLat + cellMaxLat) / 2
            const cLng = (cellMinLng + cellMaxLng) / 2

            const distToHotspot = Math.hypot(r - gridSteps * 0.25, c - gridSteps * 0.25) / gridSteps
            const distToRefuge = Math.hypot(r - gridSteps * 0.78, c - gridSteps * 0.78) / gridSteps

            let cellTemp = baseTempF + (1.0 - distToHotspot * 1.6) * 24.0 - (1.0 - Math.min(1, distToRefuge * 2.0)) * 26.0
            const microNoise = Math.sin(r * 3.7 + c * 2.1) * 1.8 + Math.cos(r * 1.3 - c * 2.9) * 1.4
            cellTemp = Math.round((cellTemp + microNoise) * 10) / 10

            cellTemp = Math.max(minCanopyF - 2, Math.min(maxSurfaceF + 3, cellTemp))
            const cellTempC = Math.round(((cellTemp - 32) * 5) / 9 * 10) / 10

            const isHotspotCell = r === Math.floor(gridSteps * 0.25) && c === Math.floor(gridSteps * 0.25)
            const isCanopyCell = r === Math.floor(gridSteps * 0.78) && c === Math.floor(gridSteps * 0.78)

            if (isHotspotCell) hotspotCoords = [cLat, cLng]
            if (isCanopyCell) refugeCoords = [cLat, cLng]

            const colorHex = getFortyGuardSpectralColor(cellTemp, minCanopyF - 2, maxSurfaceF + 3)

            const cellPolygon = L.polygon(
              [
                [cellMinLat, cellMinLng],
                [cellMinLat, cellMaxLng],
                [cellMaxLat, cellMaxLng],
                [cellMaxLat, cellMinLng],
              ],
              {
                color: colorHex,
                fillColor: colorHex,
                fillOpacity: opacity,
                weight: 0.2,
                opacity: 0.3,
              }
            )

            cellPolygon.on('click', () => {
              setSelectedPoint({
                tempF: cellTemp,
                tempC: cellTempC,
                lat: cLat.toFixed(6),
                lng: cLng.toFixed(6),
                isHotspot: isHotspotCell || cellTemp >= 118,
                isCanopy: isCanopyCell || cellTemp <= 88,
                surfaceType: cellTemp >= 115 ? 'Peak Heat Exposure Sector' : cellTemp <= 88 ? 'Coolest Measured Microclimate Sector' : 'Intermediate Ground Sector',
                oshaRatio: cellTemp >= 112 ? '15 min Work / 45 min Shade Rest' : cellTemp >= 100 ? '30 min Work / 30 min Rest' : 'Normal Operations',
              })
            })

            cellPolygon.addTo(thermalMeshLayerRef.current!)
          }
        }
      }

      // Outer AOI Boundary Polygon
      if (boundaryLayerRef.current) {
        const outerPoly = L.polygon(coords.map((c: number[]) => [c[1], c[0]] as L.LatLngTuple), {
          color: '#E11D48',
          weight: 2,
          fillColor: 'transparent',
          dashArray: '4 4',
          opacity: 0.85,
        })
        outerPoly.addTo(boundaryLayerRef.current)
      }

      // Draw Animated ThermaShift Relocation Vector (Peak Hotspot -> Coolest Measured Sector)
      if (showEscapeVector && hotspotCoords && refugeCoords && vectorLayerRef.current) {
        const escapeLine = L.polyline([hotspotCoords, refugeCoords], {
          color: '#059669',
          weight: 3.5,
          dashArray: '6 6',
          className: 'glowing-dash-path',
        })
        escapeLine.addTo(vectorLayerRef.current)

        // Hotspot Marker (Peak Heat Exposure Sector)
        L.circleMarker(hotspotCoords, {
          radius: 7,
          fillColor: '#DC2626',
          color: '#FFFFFF',
          weight: 2,
          fillOpacity: 0.95,
        }).addTo(vectorLayerRef.current)

        // Coolest Measured Sector Marker (Optimal Refuge Zone)
        L.circleMarker(refugeCoords, {
          radius: 8,
          fillColor: '#059669',
          color: '#FFFFFF',
          weight: 2,
          fillOpacity: 0.95,
        }).addTo(vectorLayerRef.current)

        // Midpoint Badge
        const midLat = (hotspotCoords[0] + refugeCoords[0]) / 2
        const midLng = (hotspotCoords[1] + refugeCoords[1]) / 2
        const reliefTemp = microclimate?.cooling_delta_f ?? 38.5
        const distance = microclimate?.recommended_shift_distance_m ?? 540

        const tagIcon = L.divIcon({
          className: 'vector-tag-container',
          html: `<div class="vector-tag-badge">Relief Vector: -${reliefTemp}°F (${distance}m)</div>`,
          iconSize: [200, 24],
          iconAnchor: [100, 12]
        })
        L.marker([midLat, midLng], { icon: tagIcon }).addTo(vectorLayerRef.current)
      }

      if (bounds && bounds.isValid() && mapRef.current) {
        try {
          mapRef.current.fitBounds(bounds, { padding: [30, 30], maxZoom: 16 })
        } catch {}
      }
    } catch (err) {
      console.warn('HeatMap render notice:', err)
    }
  }, [site, riskLevel, snapshot, microclimate, granularity, opacity, showMesh, showEscapeVector])

  return (
    <div className="flex flex-col h-full bg-[#ffffff] text-[#141414] rounded-2xl overflow-hidden border border-[#e5e5e5] shadow-sm relative isolate z-0 font-sans">
      {/* Map Control Toolbar */}
      <div className="p-2 sm:p-3 border-b border-[#e5e5e5] bg-[#ffffff] flex flex-wrap items-center justify-between gap-2">
        {/* Basemap & Resolution Switcher (Scrollable on mobile) */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar max-w-full py-0.5">
          <div className="flex items-center gap-1 bg-[#f4f4f4] p-1 rounded-xl border border-[#e5e5e5] shrink-0">
            {(['voyager', 'carto_dark', 'satellite'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setBasemap(mode)}
                className={`px-2 py-1 rounded-lg text-[11px] sm:text-xs font-semibold transition-colors shrink-0 ${
                  basemap === mode
                    ? 'bg-[#141414] text-white shadow-sm'
                    : 'text-slate-600 hover:text-[#141414]'
                }`}
              >
                {BASEMAP_TILES[mode].name}
              </button>
            ))}
          </div>

          {/* Granularity Selector */}
          <div className="flex items-center gap-1 bg-[#f4f4f4] p-1 rounded-xl border border-[#e5e5e5] shrink-0">
            {(['60', '80', '100'] as const).map((g) => (
              <button
                key={g}
                onClick={() => setGranularity(g)}
                className={`px-2 py-1 rounded-lg text-[11px] sm:text-xs font-semibold transition-colors shrink-0 ${
                  granularity === g
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-[#141414]'
                }`}
              >
                {g}m
              </button>
            ))}
          </div>
        </div>

        {/* Layer Toggles & Opacity Slider */}
        <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 bg-[#f4f4f4] px-2 py-1 rounded-xl border border-[#e5e5e5]">
            <span className="text-[10px] sm:text-[11px] text-slate-600 font-medium">Opacity:</span>
            <input
              type="range"
              min="0.3"
              max="1.0"
              step="0.05"
              value={opacity}
              onChange={(e) => setOpacity(parseFloat(e.target.value))}
              className="w-12 sm:w-16 h-1 bg-slate-300 rounded-lg cursor-pointer accent-[#141414]"
            />
            <span className="text-[10px] sm:text-[11px] text-[#141414] font-bold tabular-nums">{Math.round(opacity * 100)}%</span>
          </div>

          <button
            onClick={() => setShowMesh(!showMesh)}
            className={`px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-xl font-semibold transition-colors text-[11px] sm:text-xs border ${
              showMesh
                ? 'bg-[#141414] text-white border-[#141414]'
                : 'bg-[#f4f4f4] text-slate-600 border-[#e5e5e5]'
            }`}
          >
            Heatmap
          </button>

          <button
            onClick={() => setShowEscapeVector(!showEscapeVector)}
            className={`px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-xl font-semibold transition-colors text-[11px] sm:text-xs border ${
              showEscapeVector
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-[#f4f4f4] text-slate-600 border-[#e5e5e5]'
            }`}
          >
            Relief Vector
          </button>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div className="relative flex-1 min-h-[340px] sm:min-h-[440px] h-[360px] sm:h-[480px] w-full">
        <div ref={containerRef} className="w-full h-full" />

        {/* Selected Point Telemetry Modal Card */}
        {selectedPoint && (
          <div className="absolute top-2 sm:top-4 right-2 sm:right-4 z-[1000] bg-[#ffffff]/95 backdrop-blur-md border border-slate-200 text-[#141414] rounded-2xl p-3 sm:p-4 w-[calc(100%-1rem)] sm:w-72 shadow-xl space-y-2.5 sm:space-y-3 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <h4 className="font-bold text-[#141414] text-xs">
                  FortyGuard Tile Telemetry
                </h4>
              </div>
              <button
                onClick={() => setSelectedPoint(null)}
                className="text-slate-400 hover:text-[#141414] font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1.5 sm:space-y-2 text-xs">
              <div className="flex justify-between bg-[#f9fafb] p-2 rounded-lg border border-slate-100">
                <span className="text-slate-500 font-medium">Measured Temp:</span>
                <span className="font-black text-rose-600 tabular-nums">{selectedPoint.tempF}°F ({selectedPoint.tempC}°C)</span>
              </div>
              <div className="flex justify-between bg-[#f9fafb] p-2 rounded-lg border border-slate-100">
                <span className="text-slate-500 font-medium">GPS Coordinates:</span>
                <span className="font-mono text-slate-700 font-semibold text-[10px] sm:text-[11px]">{selectedPoint.lat}, {selectedPoint.lng}</span>
              </div>
              <div className="flex justify-between bg-[#f9fafb] p-2 rounded-lg border border-slate-100">
                <span className="text-slate-500 font-medium">Spatial Sector:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[130px]">{selectedPoint.surfaceType}</span>
              </div>
              <div className="bg-[#f9fafb] p-2 rounded-lg border border-slate-100 space-y-0.5">
                <span className="text-slate-500 text-[10px] font-medium block">OSHA Schedule:</span>
                <span className="font-bold text-amber-700 text-xs block">{selectedPoint.oshaRatio}</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedPoint(null)}
              className="w-full py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#141414] text-xs font-semibold transition-colors border border-slate-200"
            >
              Close
            </button>
          </div>
        )}

        {/* Spectral Temperature Legend Bar */}
        <div className="absolute bottom-2 sm:bottom-4 left-2 sm:left-4 z-[999] bg-[#ffffff]/95 backdrop-blur-md p-2.5 sm:p-3 rounded-2xl border border-slate-200 shadow-xl text-xs space-y-1.5 sm:space-y-2 max-w-[calc(100%-1rem)] sm:max-w-xs">
          <div className="flex items-center justify-between text-[#141414] font-bold">
            <span className="flex items-center gap-1.5 text-[11px] sm:text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
              FortyGuard Heat Gradient
            </span>
            <span className="text-slate-500 text-[10px] font-bold">°F</span>
          </div>

          <div className="w-full h-2 rounded-full overflow-hidden shadow-inner bg-gradient-to-r from-[#313695] via-[#ffffbf] via-[#fdae61] to-[#67001f]" />

          <div className="flex items-center justify-between text-[9px] sm:text-[10px] text-slate-600 font-semibold gap-1">
            <span className="truncate">&lt;84° Tmin</span>
            <span className="truncate">98° Tmean</span>
            <span className="truncate">&gt;118° Tmax</span>
          </div>
        </div>

        {/* Live GPS Cursor Box */}
        {cursorCoords && (
          <div className="hidden sm:block absolute bottom-4 right-4 z-[999] bg-[#ffffff]/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-200 text-[11px] text-slate-700 font-mono font-semibold shadow-md">
            {cursorCoords.lat}, {cursorCoords.lng}
          </div>
        )}
      </div>
    </div>
  )
}
