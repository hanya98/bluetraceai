// Reference marine environmental records for baseline evaluation.
export const environmentalByIncident = {
  'INC-024': { wind_speed: 4.2, wind_direction: 245, current_speed: 0.8, current_direction: 120, wave_height_m: 0.9, sea_surface_temperature_c: 28.1, source: 'Mock blended met-ocean field' },
  'INC-025': { wind_speed: 5.6, wind_direction: 218, current_speed: 0.6, current_direction: 142, wave_height_m: 1.2, sea_surface_temperature_c: 29.0, source: 'Mock blended met-ocean field' },
  'INC-026': { wind_speed: 3.8, wind_direction: 172, current_speed: 0.5, current_direction: 38, wave_height_m: 0.7, sea_surface_temperature_c: 29.6, source: 'Mock blended met-ocean field' },
  'INC-027': { wind_speed: 6.1, wind_direction: 198, current_speed: 0.9, current_direction: 72, wave_height_m: 1.4, sea_surface_temperature_c: 27.8, source: 'Mock blended met-ocean field' },
  'INC-028': { wind_speed: 4.7, wind_direction: 226, current_speed: 0.7, current_direction: 110, wave_height_m: 1.0, sea_surface_temperature_c: 28.7, source: 'Mock blended met-ocean field' },
}

export const environmentalData = Object.entries(environmentalByIncident).map(([incidentId, conditions]) => ({ incidentId, ...conditions }))
