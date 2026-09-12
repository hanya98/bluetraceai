import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AttributionControl,
  Map,
  NavigationControl,
  setWorkerUrl,
} from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Eye, Layers3, MapPinned, RadioTower, Route, Ship } from 'lucide-react'
import {
  calculateMapBounds,
  toFeatureCollection,
  toLineFeature,
  toPointFeature,
} from '../../utils/geo'
import { buildRegionFeatureCollection } from '../../data/marineRegions'

// Configure the MapLibre worker for Vite
setWorkerUrl(workerUrl)

const empty = {
  type: 'FeatureCollection',
  features: [],
}

const controlItems = [
  {
    key: 'regions',
    label: 'Monitoring Regions',
    icon: MapPinned,
  },
  {
    key: 'slicks',
    label: 'Potential Spill Areas',
    icon: Eye,
  },
  {
    key: 'vessels',
    label: 'AIS Vessels',
    icon: Ship,
  },
  {
    key: 'tracks',
    label: 'Vessel Tracks',
    icon: Route,
  },
  {
    key: 'corridor',
    label: 'Drift Corridor',
    icon: RadioTower,
  },
  {
    key: 'ports',
    label: 'Ports',
    icon: MapPinned,
  },
  {
    key: 'platforms',
    label: 'Offshore Platforms',
    icon: RadioTower,
  },
  {
    key: 'coastline',
    label: 'Coastline',
    icon: Route,
  },
]

const visibilityLayers = {
  regions: ['marine-regions-fill', 'marine-regions-selected', 'marine-regions-border'],
  slicks: ['slick-probability-fill', 'slick-probability-outline'],
  vessels: ['vessel-markers'],
  tracks: ['vessel-tracks'],
  corridor: ['drift-probability-fill', 'drift-probability-outline'],
  ports: ['port-markers'],
  platforms: ['platform-markers'],
  coastline: ['coastline-reference'],
}

function MapView({
  incidents,
  selectedIncident,
  vessels,
  selectedVesselId,
  slickExtent,
  driftCorridor,
  referenceLayers,
  onIncidentSelect,
  onVesselSelect,
  // Marine region grid props
  selectedRegionId,
  onRegionSelect,
  onMapClick,
}) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const callbacksRef = useRef({
    onIncidentSelect,
    onVesselSelect,
    onRegionSelect,
    onMapClick,
  })
  const hasFittedRef = useRef(false)

  const [ready, setReady] = useState(false)

  const [visibility, setVisibility] = useState({
    regions: true,
    slicks: true,
    vessels: true,
    tracks: true,
    corridor: true,
    ports: false,
    platforms: false,
    coastline: true,
  })

  // Keep callbacks up to date without recreating the map
  useEffect(() => {
    callbacksRef.current = {
      onIncidentSelect,
      onVesselSelect,
      onRegionSelect,
      onMapClick,
    }
  }, [onIncidentSelect, onVesselSelect, onRegionSelect, onMapClick])

  // Sync marine-regions GeoJSON data whenever selectedRegionId changes
  useEffect(() => {
    if (!ready || !mapRef.current) return
    const source = mapRef.current.getSource('marine-regions')
    if (source) {
      source.setData(buildRegionFeatureCollection(selectedRegionId))
    }
  }, [ready, selectedRegionId])

  // Incident points
  const incidentFeatures = useMemo(
    () =>
      toFeatureCollection(
        incidents.map((incident) =>
          toPointFeature(
            [incident.longitude, incident.latitude],
            {
              id: incident.id,
              selected: incident.id === selectedIncident?.id,
              confidence: incident.confidence,
            }
          )
        )
      ),
    [incidents, selectedIncident?.id]
  )

  // Vessel points
  const vesselFeatures = useMemo(
    () =>
      toFeatureCollection(
        vessels.map((vessel) =>
          toPointFeature(
            [vessel.longitude, vessel.latitude],
            {
              id: vessel.id,
              name: vessel.vessel_name,
              selected: vessel.id === selectedVesselId,
              score: vessel.vessel_of_interest_score,
            }
          )
        )
      ),
    [vessels, selectedVesselId]
  )

  // Vessel trajectories
  const trackFeatures = useMemo(
    () =>
      toFeatureCollection(
        vessels.map((vessel) =>
          toLineFeature(vessel.trajectory, {
            id: vessel.id,
            selected: vessel.id === selectedVesselId,
            name: vessel.vessel_name,
          })
        )
      ),
    [vessels, selectedVesselId]
  )

  // Bounds containing all incidents
  const incidentBounds = useMemo(
    () =>
      calculateMapBounds(
        incidents.map((incident) => [
          incident.longitude,
          incident.latitude,
        ])
      ),
    [incidents]
  )

  // Initialize MapLibre once
  useEffect(() => {
    if (mapRef.current || !containerRef.current) {
      return undefined
    }

    // Guard against React Strict Mode double-invocation: if this effect's
    // cleanup runs before the async 'load' event fires, we discard the result.
    let isMounted = true

    const map = new Map({
      container: containerRef.current,

      // Provide a default viewport so MapLibre always requests tiles on init.
      // The data-driven fitBounds() call below will override this once incidents load.
      center: [72.8, 18.9], // Mumbai / Indian Ocean default
      zoom: 4,

      style: {
        version: 8,

        sources: {
          satellite: {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            attribution: 'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
          },
          labels: {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
          },
        },

        layers: [
          {
            id: 'basemap-satellite',
            type: 'raster',
            source: 'satellite',
            minzoom: 0,
            maxzoom: 19,
          },
          {
            id: 'basemap-labels',
            type: 'raster',
            source: 'labels',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },

      attributionControl: false,
    })

    map.addControl(
      new NavigationControl({
        showCompass: false,
      }),
      'top-right'
    )

    map.addControl(
      new AttributionControl({
        compact: true,
      })
    )

    map.on('load', () => {
      // If the cleanup already ran (Strict Mode first pass), discard this map.
      if (!isMounted) {
        map.remove()
        return
      }

      map.resize()

      // Add GeoJSON sources
      ;[
        'incidents',
        'slicks',
        'vessels',
        'tracks',
        'corridor',
        'ports',
        'platforms',
        'coastline',
      ].forEach((id) => {
        map.addSource(id, {
          type: 'geojson',
          data: empty,
        })
      })

      // Marine monitoring regions source — populated after load
      map.addSource('marine-regions', {
        type: 'geojson',
        data: buildRegionFeatureCollection(null),
      })

      // Region fill — transparent, used only for hover/click hit-testing
      map.addLayer({
        id: 'marine-regions-fill',
        type: 'fill',
        source: 'marine-regions',
        paint: {
          'fill-color': '#1a6b9a',
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.08,
            0.03,
          ],
        },
      })

      // Selected region highlight
      map.addLayer({
        id: 'marine-regions-selected',
        type: 'fill',
        source: 'marine-regions',
        filter: ['==', ['get', 'selected'], true],
        paint: {
          'fill-color': '#1a6b9a',
          'fill-opacity': 0.14,
        },
      })

      // Region border
      map.addLayer({
        id: 'marine-regions-border',
        type: 'line',
        source: 'marine-regions',
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'selected'], true],
            '#4db6e8',
            '#2a8cbf',
          ],
          'line-width': [
            'case',
            ['==', ['get', 'selected'], true],
            2,
            1,
          ],
          'line-opacity': [
            'case',
            ['==', ['get', 'selected'], true],
            0.9,
            0.45,
          ],
          'line-dasharray': [4, 3],
        },
      })

      // Region hover state tracking
      let hoveredRegionId = null

      map.on('mousemove', 'marine-regions-fill', (event) => {
        if (event.features?.length > 0) {
          if (hoveredRegionId !== null) {
            map.setFeatureState(
              { source: 'marine-regions', id: hoveredRegionId },
              { hover: false }
            )
          }
          hoveredRegionId = event.features[0].id
          map.setFeatureState(
            { source: 'marine-regions', id: hoveredRegionId },
            { hover: true }
          )
          map.getCanvas().style.cursor = 'pointer'
        }
      })

      map.on('mouseleave', 'marine-regions-fill', () => {
        if (hoveredRegionId !== null) {
          map.setFeatureState(
            { source: 'marine-regions', id: hoveredRegionId },
            { hover: false }
          )
        }
        hoveredRegionId = null
        map.getCanvas().style.cursor = ''
      })

      map.on('click', 'marine-regions-fill', (event) => {
        const id = event.features?.[0]?.properties?.id
        if (id) {
          callbacksRef.current.onRegionSelect?.(id)
        }
      })

      map.on('click', (event) => {
        const features = map.queryRenderedFeatures(event.point, {
          layers: ['incident-markers', 'vessel-markers', 'marine-regions-fill'],
        })
        if (!features.length && callbacksRef.current.onMapClick) {
          const lngLat = event.lngLat
          const bounds = map.getBounds()
          callbacksRef.current.onMapClick({
            lat: lngLat.lat,
            lon: lngLat.lng,
            bounds: [
              [bounds.getWest(), bounds.getSouth()],
              [bounds.getEast(), bounds.getNorth()],
            ],
          })
        }
      })

      // Drift corridor
      map.addLayer({
        id: 'drift-probability-fill',
        type: 'fill',
        source: 'corridor',
        paint: {
          'fill-color': '#1d4b3b',
          'fill-opacity': 0.13,
        },
      })

      map.addLayer({
        id: 'drift-probability-outline',
        type: 'line',
        source: 'corridor',
        paint: {
          'line-color': '#1d4b3b',
          'line-width': 2,
          'line-opacity': 0.7,
          'line-dasharray': [2, 2],
        },
      })

      // Oil spill polygon
      map.addLayer({
        id: 'slick-probability-fill',
        type: 'fill',
        source: 'slicks',
        paint: {
          'fill-color': '#663520',
          'fill-opacity': 0.22,
        },
      })

      map.addLayer({
        id: 'slick-probability-outline',
        type: 'line',
        source: 'slicks',
        paint: {
          'line-color': '#663520',
          'line-width': 2,
          'line-opacity': 0.76,
          'line-dasharray': [1.4, 1.2],
        },
      })

      // Coastline
      map.addLayer({
        id: 'coastline-reference',
        type: 'line',
        source: 'coastline',
        paint: {
          'line-color': '#1d4b3b',
          'line-width': 1.5,
          'line-opacity': 0.55,
        },
      })

      // Vessel tracks
      map.addLayer({
        id: 'vessel-tracks',
        type: 'line',
        source: 'tracks',
        paint: {
          'line-color': [
            'case',
            ['get', 'selected'],
            '#663520',
            '#c16d4c',
          ],
          'line-width': [
            'case',
            ['get', 'selected'],
            4,
            2,
          ],
          'line-opacity': [
            'case',
            ['get', 'selected'],
            0.95,
            0.55,
          ],
        },
      })

      // Port markers
      map.addLayer({
        id: 'port-markers',
        type: 'circle',
        source: 'ports',
        paint: {
          'circle-color': '#663520',
          'circle-radius': 5,
          'circle-stroke-color': '#f8eadf',
          'circle-stroke-width': 1.5,
        },
      })

      // Offshore platform markers
      map.addLayer({
        id: 'platform-markers',
        type: 'circle',
        source: 'platforms',
        paint: {
          'circle-color': '#1d4b3b',
          'circle-radius': 5,
          'circle-stroke-color': '#f8eadf',
          'circle-stroke-width': 1.5,
        },
      })

      // Incident markers
      map.addLayer({
        id: 'incident-markers',
        type: 'circle',
        source: 'incidents',
        paint: {
          'circle-color': [
            'case',
            ['get', 'selected'],
            '#663520',
            '#1d4b3b',
          ],
          'circle-radius': [
            'case',
            ['get', 'selected'],
            10,
            6.5,
          ],
          'circle-stroke-color': '#f8eadf',
          'circle-stroke-width': 2.5,
        },
      })

      // Vessel markers
      map.addLayer({
        id: 'vessel-markers',
        type: 'circle',
        source: 'vessels',
        paint: {
          'circle-color': [
            'case',
            ['get', 'selected'],
            '#ffd4ba',
            '#f8eadf',
          ],
          'circle-radius': [
            'case',
            ['get', 'selected'],
            8,
            5.5,
          ],
          'circle-stroke-color': [
            'case',
            ['get', 'selected'],
            '#663520',
            '#1d4b3b',
          ],
          'circle-stroke-width': 2,
        },
      })

      // Generic feature selection handler
      const selectFeature = (layer, callback) => {
        map.on('click', layer, (event) => {
          const id =
            event.features?.[0]?.properties?.id

          if (id) {
            callback(id)
          }
        })
      }

      selectFeature(
        'incident-markers',
        (id) =>
          callbacksRef.current.onIncidentSelect?.(id)
      )

      selectFeature(
        'vessel-markers',
        (id) =>
          callbacksRef.current.onVesselSelect?.(id)
      )

      // Pointer cursor
      ;['incident-markers', 'vessel-markers'].forEach(
        (layer) => {
          map.on('mouseenter', layer, () => {
            map.getCanvas().style.cursor = 'pointer'
          })

          map.on('mouseleave', layer, () => {
            map.getCanvas().style.cursor = ''
          })
        }
      )

      mapRef.current = map
      setReady(true)
    })

    return () => {
      isMounted = false
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Update map data
  useEffect(() => {
    if (!ready || !mapRef.current) {
      return
    }

    const map = mapRef.current

    const incidentSource = map.getSource('incidents')
    const slickSource = map.getSource('slicks')
    const vesselSource = map.getSource('vessels')
    const trackSource = map.getSource('tracks')
    const corridorSource = map.getSource('corridor')
    const portSource = map.getSource('ports')
    const platformSource = map.getSource('platforms')
    const coastlineSource = map.getSource('coastline')

    incidentSource?.setData(incidentFeatures)

    slickSource?.setData(
      slickExtent
        ? toFeatureCollection([slickExtent])
        : empty
    )

    vesselSource?.setData(vesselFeatures)

    trackSource?.setData(trackFeatures)

    corridorSource?.setData(
      driftCorridor
        ? toFeatureCollection([driftCorridor])
        : empty
    )

    portSource?.setData(
      referenceLayers?.ports ?? empty
    )

    platformSource?.setData(
      referenceLayers?.platforms ?? empty
    )

    coastlineSource?.setData(
      referenceLayers?.coastline ?? empty
    )

    if (!hasFittedRef.current && incidentBounds) {
      map.fitBounds(incidentBounds, {
        padding: 70,
        maxZoom: 5.4,
        duration: 0,
      })

      hasFittedRef.current = true
    }
  }, [
    ready,
    incidentFeatures,
    vesselFeatures,
    trackFeatures,
    slickExtent,
    driftCorridor,
    referenceLayers,
    incidentBounds,
  ])

  // Fly to selected incident
  useEffect(() => {
    if (!ready || !selectedIncident || !mapRef.current) {
      return
    }

    const lat = Number(selectedIncident.latitude)
    const lon = Number(selectedIncident.longitude)

    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      mapRef.current.flyTo({
        center: [lon, lat],
        zoom: 8.4,
        duration: 850,
        essential: true,
      })
    }
  }, [ready, selectedIncident?.id, selectedIncident?.latitude, selectedIncident?.longitude])

  // Layer visibility
  useEffect(() => {
    if (!ready || !mapRef.current) {
      return
    }

    Object.entries(visibilityLayers).forEach(
      ([key, layerIds]) => {
        layerIds.forEach((layerId) => {
          if (mapRef.current.getLayer(layerId)) {
            mapRef.current.setLayoutProperty(
              layerId,
              'visibility',
              visibility[key]
                ? 'visible'
                : 'none'
            )
          }
        })
      }
    )
  }, [ready, visibility])

  return (
    <section className="relative h-[600px] min-h-[570px] w-full overflow-hidden rounded-2xl border border-[#d6b9a7] bg-[#c4e0e5] shadow-sm">
      <div
        ref={containerRef}
        className="absolute inset-0 h-full w-full"
      />

      {/* Map Layers */}
      <div className="absolute left-3 top-3 z-10 w-52 rounded-xl border border-[#e6c8b5] bg-[#fffaf6]/95 p-3 shadow-sm backdrop-blur">
        <div className="mb-2 flex items-center gap-2 text-xs font-bold tracking-[.12em] text-[#1d4b3b]">
          <Layers3 size={15} />
          MAP LAYERS
        </div>

        {controlItems.map(
          ({ key, label, icon: Icon }) => (
            <label
              className="flex cursor-pointer items-center justify-between py-1.5 text-xs text-[#4d3328]"
              key={key}
            >
              <span className="flex items-center gap-1.5">
                <Icon size={13} />
                {label}
              </span>

              <input
                type="checkbox"
                checked={visibility[key]}
                onChange={(event) =>
                  setVisibility((current) => ({
                    ...current,
                    [key]: event.target.checked,
                  }))
                }
                className="accent-[#1d4b3b]"
              />
            </label>
          )
        )}
      </div>

      {/* Intelligence Legend */}
      <div className="absolute bottom-3 left-3 z-10 rounded-xl border border-[#e6c8b5] bg-[#fffaf6]/95 p-3 text-[11px] text-[#4d3328] shadow-sm">
        <p className="mb-2 font-bold tracking-[.12em] text-[#1d4b3b]">
          INTELLIGENCE LEGEND
        </p>

        <p>
          <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full bg-[#663520]" />
          Selected candidate
        </p>

        <p>
          <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full bg-[#1d4b3b]" />
          Oil Spill Candidate
        </p>

        <p>
          <span className="mr-2 inline-block h-2.5 w-4 border border-dashed border-[#663520] bg-[#663520]/20" />
          Predicted slick probability area
        </p>

        <p>
          <span className="mr-2 inline-block h-2.5 w-4 border border-dashed border-[#1d4b3b] bg-[#1d4b3b]/10" />
          Reverse-drift probability corridor
        </p>

        <p>
          <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full border-2 border-[#1d4b3b] bg-[#f8eadf]" />
          AIS Vessel
        </p>
      </div>
    </section>
  )
}

export default MapView