import requests
import pandas as pd
import json

def fetch_solar_data(lat, lon, start, end, params=None):
    """
    Fetch solar data for a given latitude and longitude.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        params (dict, optional): Additional parameters for the API request.
    """
    base_url = 'https://power.larc.nasa.gov/api/temporal/hourly/point'
    default_params = {
        'parameters': 'ALLSKY_SFC_SW_DWN',
        'community': 'RE',
        'format': 'JSON',
        'units': 'metric',
        'user': 'leobigott98',
        'time-standard': 'utc',
        'start': start,
        'end': end,
        'latitude': lat,
        'longitude': lon
    }
    if params:
        default_params.update(params)
    
    response = requests.get(base_url, params=default_params)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Example usage
    latitude = 34.05  # Los Angeles
    longitude = -118.25
    start_date = '20220101'
    end_date = '20220107'
    
    solar_data = fetch_solar_data(latitude, longitude, start_date, end_date)
    print(solar_data)