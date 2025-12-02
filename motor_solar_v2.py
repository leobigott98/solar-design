import pandas as pd
import matplotlib.pyplot as plt
import pvlib
from pvlib.location import Location
import math

# ==========================================
# 1. EL MOTOR SOLAR (Usando pvlib)
# ==========================================
def simular_curva_solar(lat, lon, fecha, potencia_pico_kw, eficiencia=0.85):
    """
    Usa pvlib para simular la irradiancia en un día despejado (Clear Sky).
    Devuelve un DataFrame con la potencia generada hora a hora.
    """
    tz = 'America/Caracas'
    
    # Crear objeto de ubicación
    site = Location(lat, lon, tz=tz)
    
    # Crear rango de fechas (un día completo, frecuencia 1 hora)
    times = pd.date_range(start=f'{fecha} 00:00', end=f'{fecha} 23:59', freq='1h', tz=tz)
    
    # Calcular posición solar
    solpos = site.get_solarposition(times)
    
    # Modelo de Cielo Despejado (Ineichen) - Ideal para dimensionamiento base
    clearsky = site.get_clearsky(times)
    
    # GHI = Global Horizontal Irradiance (Radiación total)
    # Estimación simple: Potencia = GHI * (Area/1000) * Eficiencia... 
    # Simplifiquemos: Potencia Salida = (GHI / 1000 W/m2) * Potencia_Instalada_kW * Eficiencia
    
    generacion_kw = (clearsky['ghi'] / 1000) * potencia_pico_kw * eficiencia
    
    # Limpiamos valores negativos (noche)
    generacion_kw[generacion_kw < 0] = 0
    
    return generacion_kw

# ==========================================
# 2. EL MOTOR DE BATERÍAS (Con Corrección Térmica)
# ==========================================
def calcular_baterias_termico(consumo_diario_kwh, dias_autonomia, voltaje, capacidad_modulo_ah, temp_ambiente):
    """
    Calcula baterías aplicando corrección por temperatura.
    """
    # Lógica de Factor de Temperatura (Simplificada para MVP)
    # Temperatura ideal: 25°C (Factor 1.0)
    
    if temp_ambiente < 20: 
        # FRÍO (Mérida): La batería rinde menos. Castigo fuerte.
        # Por cada 10°C menos, pierdes aprox 10-15% capacidad en Plomo/Litio
        factor_temp = 0.85 
        estado = "❄️ Frío (Mérida/Andes) - Rendimiento químico bajo"
        
    elif temp_ambiente > 30:
        # CALOR (Maracaibo): 
        # Aunque la capacidad sube químicamente, sobredimensionamos para
        # reducir la corriente de descarga y evitar sobrecalentamiento (C-rate bajo).
        factor_temp = 0.90 
        estado = "🔥 Calor (Maracaibo/Costa) - Derateo por protección térmica"
        
    else:
        # TEMPLADO (Caracas)
        factor_temp = 1.0
        estado = "✅ Templado (Ideal)"

    dod = 0.8 # Profundidad de descarga (Litio)
    
    # Energía real que necesitamos guardar (incluyendo margen por temperatura)
    energia_reserva_kwh = consumo_diario_kwh * dias_autonomia
    
    # Capacidad requerida ajustada
    capacidad_total_ah = (energia_reserva_kwh * 1000) / (voltaje * dod * factor_temp)
    
    cantidad_baterias = math.ceil(capacidad_total_ah / capacidad_modulo_ah)
    
    return cantidad_baterias, estado, capacidad_total_ah

# ==========================================
# 3. EJECUCIÓN DEL ESCENARIO
# ==========================================

# Datos de entrada
consumo_diario = 5.0 # kWh
potencia_solar_instalada = 1.2 # kWp (aprox 3 paneles de 400W)
fecha_simulacion = '2024-06-21' # Solsticio (Día largo)

# --- A. Comparación Climática (Tu petición de Maracaibo vs Mérida) ---
print("\n--- 🔋 ANÁLISIS DE BATERÍAS POR CLIMA ---")
pila_unit_ah = 100 # Batería de 100Ah
voltaje_sys = 24

# Caso Mérida (15°C)
num_merida, status_m, cap_m = calcular_baterias_termico(consumo_diario, 1.5, voltaje_sys, pila_unit_ah, 15)
print(f"MÉRIDA (15°C): {num_merida} Baterías. ({status_m})")

# Caso Maracaibo (35°C)
num_mcbo, status_z, cap_z = calcular_baterias_termico(consumo_diario, 1.5, voltaje_sys, pila_unit_ah, 35)
print(f"MARACAIBO (35°C): {num_mcbo} Baterías. ({status_z})")

# --- B. Simulación Solar con pvlib (Los Roques) ---
lat_roques, lon_roques = 11.95, -66.67
curva_solar = simular_curva_solar(lat_roques, lon_roques, fecha_simulacion, potencia_solar_instalada)

# Creamos un perfil de consumo "dummy" (Más alto en la noche)
# 24 horas de consumo. Digamos que es bajo de día (0.1 kW) y alto de noche (0.4 kW)
perfil_consumo = [0.1] * 18 + [0.4] * 6 # Un ejemplo simple
perfil_consumo = pd.Series(perfil_consumo, index=curva_solar.index) 

# ==========================================
# 4. GRAFICAR (Matplotlib)
# ==========================================
plt.figure(figsize=(10, 6))

# Rellenar el área de generación solar
plt.fill_between(curva_solar.index, curva_solar, color='orange', alpha=0.4, label='Generación Solar (pvlib)')
plt.plot(curva_solar.index, curva_solar, color='darkorange')

# Línea de consumo
plt.step(perfil_consumo.index, perfil_consumo, color='blue', where='mid', label='Consumo Estimado', linewidth=2)

# Decoración
plt.title(f'Balance Energético en Los Roques ({fecha_simulacion})')
plt.ylabel('Potencia (kW)')
plt.xlabel('Hora del día')
plt.grid(True, alpha=0.3)
plt.legend()
plt.xticks(rotation=45)

# Mostrar
plt.tight_layout()
plt.show()

print("\n✅ Gráfica generada. Nota cómo la campana solar (naranja) debe cubrir el área azul.")