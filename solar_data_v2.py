import requests
import pandas as pd
import json

def obtener_datos_nasa(lat, lon, año_inicio, año_fin):
    """
    Obtiene datos de radiación solar y temperatura de la API NASA POWER.
    
    Parámetros:
        lat (float): Latitud.
        lon (float): Longitud.
        año_inicio (int): Año de inicio (ej. 2021).
        año_fin (int): Año fin (ej. 2022).
    """
    
    # URL base de la API de la NASA (Datos diarios)
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Parámetros técnicos:
    # ALLSKY_SFC_SW_DWN: Radiación solar incidente (kWh/m2/día)
    # T2M: Temperatura a 2 metros (°C)
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,T2M",
        "community": "RE", # Renewable Energy
        "longitude": lon,
        "latitude": lat,
        "start": f"{año_inicio}0101",
        "end": f"{año_fin}1231",
        "format": "JSON"
    }

    print(f"📡 Conectando con satélites de la NASA para coordenadas: {lat}, {lon}...")
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extraer las series de tiempo
        solar = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
        temp = data['properties']['parameter']['T2M']
        
        # Crear DataFrame de Pandas
        df = pd.DataFrame({
            'Fecha': pd.to_datetime(list(solar.keys())),
            'Radiacion_kWh_m2': list(solar.values()),
            'Temperatura_C': list(temp.values())
        })
        
        # Limpiar datos (-999 indica error en NASA POWER)
        df = df[df['Radiacion_kWh_m2'] != -999]
        
        print("✅ Datos descargados exitosamente.")
        return df
    else:
        print("❌ Error en la conexión:", response.status_code)
        return None

# --- PRUEBA: Coordenadas del Gran Roque, Venezuela ---
lat_roques = 11.95
lon_roques = -66.67

df_resultado = obtener_datos_nasa(lat_roques, lon_roques, 2022, 2023)

if df_resultado is not None:
    print(df_resultado.head()) # Muestra las primeras 5 filas
    print(f"\nPromedio de radiación diaria: {df_resultado['Radiacion_kWh_m2'].mean():.2f} kWh/m2/día")