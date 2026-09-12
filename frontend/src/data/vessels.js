// Synthetic AIS-like records. Names, MMSIs, and tracks are demonstration data only.
export const vesselsByIncident = {
  'INC-024': [
    { id: 'VOI-024-A', vessel_name: 'MT Konkan Star', mmsi: '419900241', vessel_type: 'Product tanker', latitude: 18.969, longitude: 72.746, speed: 11.8, heading: 318, vessel_of_interest_score: 0.81, distance_km: 7.4, corridor_overlap: 0.76, time_feasibility: 0.88, ais_gap_minutes: 34, trajectory: [[72.64, 18.84], [72.68, 18.88], [72.71, 18.92], [72.746, 18.969]] },
    { id: 'VOI-024-B', vessel_name: 'MV Sahyadri Trader', mmsi: '419900318', vessel_type: 'General cargo', latitude: 18.884, longitude: 72.858, speed: 9.4, heading: 142, vessel_of_interest_score: 0.46, distance_km: 6.8, corridor_overlap: 0.41, time_feasibility: 0.63, ais_gap_minutes: 0, trajectory: [[72.93, 18.96], [72.90, 18.93], [72.88, 18.90], [72.858, 18.884]] },
  ],
  'INC-025': [
    { id: 'VOI-025-A', vessel_name: 'MT Gulf Mariner', mmsi: '419900425', vessel_type: 'Crude oil tanker', latitude: 22.714, longitude: 69.593, speed: 10.6, heading: 297, vessel_of_interest_score: 0.73, distance_km: 11.2, corridor_overlap: 0.68, time_feasibility: 0.77, ais_gap_minutes: 22, trajectory: [[69.48, 22.66], [69.52, 22.68], [69.56, 22.70], [69.593, 22.714]] },
    { id: 'VOI-025-B', vessel_name: 'MV Kutch Pioneer', mmsi: '419900489', vessel_type: 'Bulk carrier', latitude: 22.644, longitude: 69.717, speed: 8.1, heading: 131, vessel_of_interest_score: 0.37, distance_km: 8.9, corridor_overlap: 0.29, time_feasibility: 0.54, ais_gap_minutes: 0, trajectory: [[69.78, 22.70], [69.75, 22.68], [69.73, 22.66], [69.717, 22.644]] },
  ],
  'INC-026': [
    { id: 'VOI-026-A', vessel_name: 'MT Coromandel Dawn', mmsi: '419900506', vessel_type: 'Chemical tanker', latitude: 13.211, longitude: 80.396, speed: 12.3, heading: 187, vessel_of_interest_score: 0.69, distance_km: 9.6, corridor_overlap: 0.62, time_feasibility: 0.79, ais_gap_minutes: 16, trajectory: [[80.42, 13.34], [80.41, 13.30], [80.40, 13.25], [80.396, 13.211]] },
    { id: 'VOI-026-B', vessel_name: 'MV Eastern Pearl', mmsi: '419900551', vessel_type: 'Container ship', latitude: 13.156, longitude: 80.511, speed: 14.2, heading: 48, vessel_of_interest_score: 0.32, distance_km: 12.4, corridor_overlap: 0.17, time_feasibility: 0.42, ais_gap_minutes: 0, trajectory: [[80.43, 13.10], [80.46, 13.12], [80.49, 13.14], [80.511, 13.156]] },
  ],
  'INC-027': [
    { id: 'VOI-027-A', vessel_name: 'MT Bay Navigator', mmsi: '419900624', vessel_type: 'Oil products tanker', latitude: 18.345, longitude: 87.031, speed: 10.1, heading: 264, vessel_of_interest_score: 0.78, distance_km: 6.1, corridor_overlap: 0.72, time_feasibility: 0.85, ais_gap_minutes: 41, trajectory: [[87.17, 18.37], [87.12, 18.36], [87.08, 18.35], [87.031, 18.345]] },
    { id: 'VOI-027-B', vessel_name: 'MV Delta Passage', mmsi: '419900677', vessel_type: 'General cargo', latitude: 18.265, longitude: 87.184, speed: 7.6, heading: 122, vessel_of_interest_score: 0.44, distance_km: 10.8, corridor_overlap: 0.35, time_feasibility: 0.57, ais_gap_minutes: 8, trajectory: [[87.10, 18.22], [87.13, 18.24], [87.16, 18.25], [87.184, 18.265]] },
  ],
  'INC-028': [
    { id: 'VOI-028-A', vessel_name: 'MT Malabar Crest', mmsi: '419900744', vessel_type: 'Oil products tanker', latitude: 10.584, longitude: 75.723, speed: 11.2, heading: 332, vessel_of_interest_score: 0.66, distance_km: 13.7, corridor_overlap: 0.58, time_feasibility: 0.74, ais_gap_minutes: 19, trajectory: [[75.61, 10.49], [75.65, 10.53], [75.69, 10.56], [75.723, 10.584]] },
    { id: 'VOI-028-B', vessel_name: 'MV Lakshadweep Link', mmsi: '419900798', vessel_type: 'Ro-ro passenger', latitude: 10.664, longitude: 75.845, speed: 15.4, heading: 148, vessel_of_interest_score: 0.21, distance_km: 15.2, corridor_overlap: 0.08, time_feasibility: 0.31, ais_gap_minutes: 0, trajectory: [[75.93, 10.74], [75.90, 10.71], [75.87, 10.68], [75.845, 10.664]] },
  ],
}

export const vessels = Object.entries(vesselsByIncident).flatMap(([incidentId, records]) => records.map((record) => ({ ...record, incidentId })))
