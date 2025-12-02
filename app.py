import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pvlib.location import Location
import math
import numpy as np

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Saman Energy: Diseño para Microgrids",
    page_icon="🌳",
    layout="wide"
)
# ==========================================
# 1. MOTOR DE CÁLCULO (BACKEND)
# ==========================================

def calcular_arrhenius_factor(temp_amb):
    """
    Calcula el factor de corrección de vida útil/capacidad basado en temperatura.
    Regla general: Por cada 10°C sobre 25°C, la degradación se acelera x2.
    Para diseño (sizing), penalizamos la capacidad disponible.
    """
    if temp_amb <= 25:
        return 1.0, "✅ Óptimo"
    
    # Modelo simplificado de degradación térmica
    delta_t = temp_amb - 25
    # Factor de castigo: Reducimos un % por cada grado extra para asegurar vida útil
    # (Esto simula que necesitamos un banco más grande para no estresarlo con calor)
    factor = 1 / (1 + (delta_t * 0.02)) # 2% de "castigo" por grado extra
    
    return factor, "🔥 Calor (Degradación Acelerada)"

def dimensionar_sistema_completo(lat, lon, consumo_diario_kwh, dias_autonomia, temp_amb, tipo_bat, potencia_panel_w):
    # --- A. BATERÍAS ---
    voltaje_sistema = 48 # Estándar para microgrids
    
    if tipo_bat == "Litio (LiFePO4)":
        dod = 0.90
        cap_modulo = 100 # Ah (ej. Pylontech US3000)
        nombre_bat = "Módulo Litio 48V"
    else:
        dod = 0.50
        cap_modulo = 200 # Ah (ej. Gel 12V en series de 4)
        nombre_bat = "Banco Plomo-Gel"
        
    # Factor Arrhenius
    factor_temp, estado_termico = calcular_arrhenius_factor(temp_amb)
    
    # Energía a almacenar
    energia_req_wh = consumo_diario_kwh * 1000 * dias_autonomia
    
    # Capacidad Banco (Ah) = Energía / (Voltaje * DoD * FactorTemp)
    capacidad_requerida_banco_ah = energia_req_wh / (voltaje_sistema * dod * factor_temp)
    num_baterias = math.ceil(capacidad_requerida_banco_ah / (cap_modulo * dod))
    capacidad_real_instalada = num_baterias * (cap_modulo * dod)


    # --- B. PANELES SOLARES ---
    # HSP Estimadas (Usando pvlib clearsky integrado simplificado)
    tz = 'America/Caracas'
    eficienca_sistema = 0.85
    site = Location(lat, lon, tz=tz)
    times = pd.date_range(start='2024-06-21 00:00', end='2024-06-21 23:59', freq='1h', tz=tz)
    clearsky = site.get_clearsky(times)
    hsp = clearsky['ghi'].sum() / 1000 # Convertir radiación total a Horas Sol Pico
    
    # Factor de seguridad (1.3) para recuperar carga
    energia_generacion_objetivo = consumo_diario_kwh * 1000 * 1.3
    
    # Generación de 1 panel
    gen_un_panel = potencia_panel_w * hsp * eficienca_sistema 
    
    num_paneles = math.ceil(energia_generacion_objetivo / gen_un_panel)
    potencia_pico_kw = (num_paneles * potencia_panel_w) / 1000
    
    # Curva de generación para gráfica (escalada al sistema diseñado)
    curva_potencia = (clearsky['ghi'] / 1000) * potencia_pico_kw * 0.85
    curva_potencia[curva_potencia < 0] = 0

    return {
        "bat": {
            "num": num_paneles, # Fix temporal variable name reuse
            "cantidad": num_baterias,
            "cap_total": round(capacidad_real_instalada,2),
            "cap_req": round(capacidad_requerida_banco_ah,2),
            "tipo": nombre_bat,
            "estado": estado_termico,
            "factor_t": factor_temp,
            "cap_modulo": cap_modulo, 
            "dod": dod
        },
        "solar": {
            "cantidad": num_paneles,
            "potencia_unit": potencia_panel_w,
            "potencia_total": potencia_pico_kw,
            "hsp": hsp,
            "curva": curva_potencia,
            "eficiencia_sistema": eficienca_sistema
        }
    }

# ==========================================
# 2. INTERFAZ GRÁFICA (FRONTEND)
# ==========================================

# st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sun_symbol.svg/1200px-Sun_symbol.svg.png", width=50)
st.sidebar.title("Configuración")

# Inputs en Sidebar
lat = st.sidebar.number_input("Latitud", min_value=-90.0, max_value=90.0, value=11.95)
lon = st.sidebar.number_input("Longitud", min_value=-180.0, max_value=180.0, value=-66.67)
temp = st.sidebar.slider("Temperatura (°C)", 15, 45, 30)
st.sidebar.markdown("---")
consumo = st.sidebar.number_input("Consumo Diario (kWh)", min_value=0.5, max_value=250.0, value=5.0, step=0.5)
dias_aut = st.sidebar.slider("Días Autonomía", 0.5, 5.0, 1.5)
tipo_bat = st.sidebar.selectbox("Batería", ["Litio (LiFePO4)", "Plomo-Ácido"])
panel_w = st.sidebar.selectbox("Potencia Panel (W)", [250, 350, 450, 550, 600])

# Título Principal
st.title("🌳 Saman Energy: Diseño para Microgrids")
st.markdown("""
Esta herramienta dimensiona sistemas fotovoltaicos enfocados en la **resiliencia** para zonas con inestabilidad eléctrica (Venezuela/Latam).
""")
st.markdown(f"**Ubicación:** Lat {lat}, Lon {lon} | **Temp:** {temp}°C")

# --- CÁLCULOS ---
res = dimensionar_sistema_completo(lat, lon, consumo, dias_aut, temp, tipo_bat, panel_w)

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard de Diseño", "🗺️ Mapa de Ubicación", "📐 Explicación Técnica", "🛠️ Detalles de Equipos"])

with tab1:
    # FILA 1: KPIs SOLARES
    st.subheader("☀️ Dimensionamiento Fotovoltaico")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Paneles Necesarios", f"{res['solar']['cantidad']} uds", f"{panel_w} Wp c/u")
    c2.metric("Potencia Array", f"{res['solar']['potencia_total']:.2f} kWp", "Total Instalado")
    c3.metric("Horas Sol Pico", f"{res['solar']['hsp']:.1f} HSP", "Calculado c/ pvlib")
    c4.metric("Eficiencia del Sistema", f"{res['solar']['eficiencia_sistema']*100:.1f} %", "Estimado")
    c5.metric("Generación Est.", f"{(res['solar']['curva'].sum()):.1f} kWh/día", "vs 1.3x Consumo")

    st.divider()

    # FILA 2: KPIs BATERÍAS
    st.subheader("🔋 Banco de Baterías (Resiliencia)")
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Baterías (Módulos)", f"{res['bat']['cantidad']} uds", res['bat']['tipo'] + ' ' + str(res['bat']['cap_modulo']) + 'Ah')
    b2.metric("Capacidad Real Instalada", f"{res['bat']['cap_total']} Ah", str(res['bat']['dod']*100) + "% DoD")
    b3.metric("Capacidad Requerida", f"{res['bat']['cap_req']} Ah", "@ 48V")
    b4.metric("Factor Térmico", f"{res['bat']['factor_t']:.2f}", res['bat']['estado'], delta_color="off")
    b5.metric("Energía Reserva", f"{(res['bat']['cap_total']*48/1000):.2f} kWh", f"Para {dias_aut} días")

    # GRÁFICA
    st.subheader("📈 Balance Energético")
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Área Solar
    ax.fill_between(res['solar']['curva'].index, res['solar']['curva'], color='#FFC107', alpha=0.5, label='Generación Solar')
    ax.plot(res['solar']['curva'].index, res['solar']['curva'], color='#FF9800', linewidth=2)
    
    # Línea de Consumo
    consumo_prom = consumo / 24
    ax.axhline(consumo_prom, color='#2196F3', linestyle='--', linewidth=2, label='Consumo Promedio')
    
    ax.set_title("Perfil de Generación Diaria (Día Claro)")
    ax.set_ylabel("Potencia (kW)")
    ax.legend()
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)

with tab2:
    # Mapa interactivo simple
    map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    st.map(map_data, zoom=10)

with tab3:
    st.header("🧮 Fórmulas Utilizadas")
    st.markdown("A continuación se detallan los modelos matemáticos implementados en el backend:")
    
    st.subheader("1. Energía Requerida (Baterías)")
    st.latex(r'''
        E_{req} = Consumo_{diario} \times Días_{autonomia}
    ''')
    
    st.subheader("2. Capacidad del Banco (Ah)")
    st.markdown("Se aplica corrección por temperatura (Modelo Arrhenius simplificado) y Profundidad de Descarga (DoD).")
    st.latex(r'''
        C_{Ah} = \frac{E_{req}}{V_{sys} \times DoD \times k_{temp}}
    ''')
    st.info("Donde $k_{temp}$ penaliza la capacidad si $T > 25^{\circ}C$.")
    
    st.subheader("3. Número de Paneles")
    st.latex(r'''
        N_{pv} = \frac{Consumo \times 1.3}{P_{panel} \times HSP \times \eta_{sys}}
    ''')
    st.markdown("*El factor 1.3 asegura que el sistema pueda recargar las baterías al día siguiente de un apagón.*")

with tab4:
    st.header("📋 Lista de Materiales (BOM Estimado)")
    
    st.write(f"""
    Para cumplir con los requisitos en **Lat: {lat}, Lon: {lon}**:
    
    * **Generación:** Se requieren **{res['solar']['cantidad']} paneles** de {panel_w}W. 
        * *Sugerencia de Conexión:* {math.ceil(res['solar']['cantidad']/2)} Strings de 2 paneles (dependiendo del controlador).
    * **Almacenamiento:** Se requieren **{res['bat']['cantidad']} módulos** de batería.
        * *Tecnología:* {tipo_bat}.
        * *Peso estimado:* {res['bat']['cantidad'] * (30 if 'Litio' in tipo_bat else 60)} kg.
    """)
    
    st.warning("⚠️ Nota: El diseño de cableado e inversores se implementará en la Fase 2.")

# Footer
st.caption("Desarrollado para Diseño de BESS en Zonas Aisladas | v1.0 MVP")