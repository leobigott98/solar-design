import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pvlib
from pvlib.location import Location
import math

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Saman Energy: Diseño para Microgrids",
    page_icon="🌳",
    layout="wide"
)

# --- 1. FUNCIONES DEL MOTOR (BACKEND) ---
# (Aquí pegamos la lógica que ya validaste)

def simular_curva_solar(lat, lon, potencia_pico_kw):
    """Simula generación solar (Clear Sky) con pvlib"""
    tz = 'America/Caracas'
    site = Location(lat, lon, tz=tz)
    times = pd.date_range(start='2024-06-21 00:00', end='2024-06-21 23:59', freq='1h', tz=tz)
    clearsky = site.get_clearsky(times)
    # Eficiencia sistema 0.85
    generacion = (clearsky['ghi'] / 1000) * potencia_pico_kw * 0.85 
    generacion[generacion < 0] = 0
    return generacion

def calcular_baterias(consumo_kwh, dias_autonomia, temp_amb, tipo_bat):
    """Calcula banco de baterías con factor térmico"""
    voltaje = 24 # Estándar para MVP
    
    # Factores según tipo
    if tipo_bat == "Litio (LiFePO4)":
        dod = 0.9
        cap_unit = 100 # Ah (ej. Pylontech)
    else: # Plomo-Ácido
        dod = 0.5
        cap_unit = 200 # Ah (ej. Gel)
    
    # Factor Térmico (Tu lógica de la semana 2)
    if temp_amb > 30:
        factor_t = 0.90 # Castigo por calor
        mensaje = "🔥 Alerta: Calor Extremo. Se sobredimensiona para proteger vida útil."
    elif temp_amb < 20:
        factor_t = 0.85 # Castigo por frío
        mensaje = "❄️ Alerta: Frío. Eficiencia química reducida."
    else:
        factor_t = 1.0
        mensaje = "✅ Temperatura Ideal."
        
    energia_req = consumo_kwh * dias_autonomia * 1000 # Wh
    capacidad_total = energia_req / (voltaje * dod * factor_t)
    num_baterias = math.ceil(capacidad_total / cap_unit)
    
    return num_baterias, capacidad_total, mensaje, cap_unit

# --- 2. INTERFAZ GRÁFICA (FRONTEND) ---

# Título y Descripción
st.title("🌳 Saman Energy: Diseño para Microgrids")
st.markdown("""
Esta herramienta dimensiona sistemas fotovoltaicos enfocados en la **resiliencia** para zonas con inestabilidad eléctrica (Venezuela/Latam).
""")

# Dividimos la pantalla en 3 columnas para Inputs Clave
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📍 Ubicación")
    lat = st.number_input("Latitud", value=11.95) # Los Roques
    lon = st.number_input("Longitud", value=-66.67)
    temp = st.slider("Temperatura Promedio (°C)", 0, 45, 30)

with col2:
    st.subheader("🏠 Consumo Crítico")
    consumo = st.number_input("Consumo Diario (kWh)", value=5.0, step=0.5)
    dias = st.slider("Días de Autonomía (Resiliencia)", 0.5, 3.0, 1.5)

with col3:
    st.subheader("⚙️ Tecnología")
    tipo_bat = st.selectbox("Tipo de Batería", ["Litio (LiFePO4)", "Plomo-Ácido (GEL)"])
    potencia_pv = st.number_input("Potencia Solar (kWp)", value=2.0, step=0.5)

st.divider()

# --- 3. CÁLCULOS EN TIEMPO REAL ---

# Ejecutar funciones
num_bat, cap_total, msg_bat, cap_unit = calcular_baterias(consumo, dias, temp, tipo_bat)
curva_solar = simular_curva_solar(lat, lon, potencia_pv)
energia_solar_dia = curva_solar.sum()

# --- 4. RESULTADOS VISUALES ---

# Fila de KPIs (Métricas Grandes)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Baterías Necesarias", f"{num_bat} Unid.", delta=f"{cap_unit}Ah @ 24V")
kpi2.metric("Capacidad Banco", f"{int(cap_total)} Ah", delta="Total")
kpi3.metric("Generación Solar Est.", f"{energia_solar_dia:.1f} kWh/día", 
            delta_color="normal" if energia_solar_dia > consumo else "inverse",
            delta=f"Vs Consumo {consumo} kWh")
kpi4.metric("Estado Térmico", f"{temp}°C", delta=msg_bat, delta_color="off")

# Advertencia si falta sol
if energia_solar_dia < consumo:
    st.error(f"⚠️ ¡Cuidado! Generas {energia_solar_dia:.1f} kWh pero consumes {consumo} kWh. El sistema se descargará.")
else:
    st.success("✅ Sistema Balanceado: La generación supera el consumo diario.")

# Gráficas y Mapa
tab1, tab2 = st.tabs(["📊 Análisis Energético", "🗺️ Mapa de Ubicación"])

with tab1:
    # Gráfica Matplotlib
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(curva_solar.index, curva_solar, color='orange', alpha=0.4, label='Generación Solar')
    ax.plot(curva_solar.index, curva_solar, color='darkorange')
    # Línea de consumo promedio (simplificada como línea recta para el MVP)
    consumo_promedio_kw = consumo / 24
    ax.axhline(y=consumo_promedio_kw, color='blue', linestyle='--', label='Consumo Promedio')
    
    ax.set_title("Perfil de Generación Diaria (Día Claro)")
    ax.set_ylabel("Potencia (kW)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)

with tab2:
    # Mapa interactivo simple
    map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    st.map(map_data, zoom=10)

# Footer
st.caption("Desarrollado para Diseño de BESS en Zonas Aisladas | v1.0 MVP")
