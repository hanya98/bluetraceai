"""
external/weather_client.py
==========================
Open-Meteo API client for wind speed, direction, and marine ocean data.
Public API — requires no auth key.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class WeatherClient:
    """Async client for Open-Meteo historical/forecast wind and marine ocean data."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"

    async def get_wind_data(
        self,
        lat: float,
        lon: float,
        timestamp_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch wind speed, wind direction, wave height, wave direction,
        ocean current velocity, current direction, and SST for given lat/lon.
        Merges responses from Open-Meteo Forecast API (wind) and Marine API (ocean).
        """
        wind_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wind_speed_10m,wind_direction_10m",
            "wind_speed_unit": "ms",
        }

        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",
        }

        result: Dict[str, Any] = {
            "wind_speed_ms": None,
            "wind_direction_deg": None,
            "wave_height_m": None,
            "wave_direction_deg": None,
            "ocean_current_velocity_ms": None,
            "ocean_current_direction_deg": None,
            "sea_surface_temperature_c": None,
            "source": "Open-Meteo Weather & Marine API",
            "is_modelled": True,
            "timestamp": None,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.HTTP_TIMEOUT) as client:
                # Fetch wind weather data
                try:
                    resp = await client.get(self.forecast_url, params=wind_params)
                    if resp.status_code == 200:
                        data = resp.json()
                        curr = data.get("current", {})
                        curr_weather = data.get("current_weather", {})

                        wind_speed = (
                            curr.get("wind_speed_10m")
                            if "wind_speed_10m" in curr
                            else curr_weather.get("windspeed")
                        )
                        wind_dir = (
                            curr.get("wind_direction_10m")
                            if "wind_direction_10m" in curr
                            else curr_weather.get("winddirection")
                        )
                        time_val = curr.get("time") or curr_weather.get("time")

                        if wind_speed is not None:
                            result["wind_speed_ms"] = round(float(wind_speed), 2)
                        if wind_dir is not None:
                            result["wind_direction_deg"] = round(float(wind_dir), 1)
                        if time_val:
                            s = str(time_val)
                            result["timestamp"] = s if s.endswith("Z") else f"{s}Z"
                    else:
                        logger.warning(
                            f"Open-Meteo forecast API HTTP {resp.status_code}: {resp.text}"
                        )
                except Exception as e:
                    logger.warning(f"Open-Meteo wind API call failed: {e}")

                # Fetch marine ocean weather data (waves, currents, SST)
                try:
                    m_resp = await client.get(self.marine_url, params=marine_params)
                    if m_resp.status_code == 200:
                        m_curr = m_resp.json().get("current", {})
                        if "wave_height" in m_curr and m_curr["wave_height"] is not None:
                            result["wave_height_m"] = round(float(m_curr["wave_height"]), 2)
                        if "wave_direction" in m_curr and m_curr["wave_direction"] is not None:
                            result["wave_direction_deg"] = round(float(m_curr["wave_direction"]), 1)
                        if "ocean_current_velocity" in m_curr and m_curr["ocean_current_velocity"] is not None:
                            val = float(m_curr["ocean_current_velocity"])
                            current_ms = val / 3.6 if val > 5.0 else val
                            result["ocean_current_velocity_ms"] = round(current_ms, 2)
                        if "ocean_current_direction" in m_curr and m_curr["ocean_current_direction"] is not None:
                            result["ocean_current_direction_deg"] = round(float(m_curr["ocean_current_direction"]), 1)
                        if "sea_surface_temperature" in m_curr and m_curr["sea_surface_temperature"] is not None:
                            result["sea_surface_temperature_c"] = round(float(m_curr["sea_surface_temperature"]), 1)
                    else:
                        logger.warning(
                            f"Open-Meteo marine API HTTP {m_resp.status_code}: {m_resp.text}"
                        )
                except Exception as e:
                    logger.warning(f"Open-Meteo marine API call failed: {e}")

        except Exception as e:
            logger.warning(f"Weather API client error ({e}). Returning available fields.")

        # If both wind and marine failed, set source accordingly
        if result["wind_speed_ms"] is None and result["wave_height_m"] is None:
            result["source"] = "Open-Meteo Marine (Unavailable)"

        return result


