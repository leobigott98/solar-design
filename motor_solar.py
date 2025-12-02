import math

class GeneradorSolar:
    def __init__(self, potencia_panel_w, eficiencia_sistema=0.85):
        """
        potencia_panel_w: Watts pico del panel que piensas usar (ej. 450W, 550W).
        eficiencia_sistema: Pérdidas por cableado, suciedad y calor (0.85 es estándar).
        """
        self.potencia_panel = potencia_panel_w
        self.eficiencia = eficiencia_sistema

    def calcular_HSP(self, radiacion_nasa_kwh_m2):
        """
        Convierte radiación bruta a Horas Sol Pico.
        Matemáticamente 1 kWh/m2 de irradiación ≈ 1 Hora a 1000 W/m2.
        """
        return radiacion_nasa_kwh_m2

    def dimensionar_arreglo(self, consumo_diario_wh, radiacion_promedio, factor_seguridad=1.3):
        """
        Calcula cuántos paneles necesitas para cubrir el consumo + pérdidas + recarga rápida.
        """
        hsp = self.calcular_HSP(radiacion_promedio)
        
        # Fórmula: Energía necesaria / (Generación de 1 panel en ese lugar)
        energia_objetivo = consumo_diario_wh * factor_seguridad
        generacion_un_panel = self.potencia_panel * hsp * self.eficiencia
        
        numero_paneles = math.ceil(energia_objetivo / generacion_un_panel)
        
        potencia_pico_total_kw = (numero_paneles * self.potencia_panel) / 1000
        
        return {
            "numero_paneles": numero_paneles,
            "potencia_total_kw": potencia_pico_total_kw,
            "generacion_diaria_estimada_kwh": round(numero_paneles * generacion_un_panel / 1000, 2),
            "hsp_usadas": hsp
        }

# --- UNIFICACIÓN: Probemos todo junto ---

# Supongamos que del PASO 1 (NASA) obtuviste este dato para Los Roques:
radiacion_los_roques = 6.5  # kWh/m2/día (Dato típico del Caribe)

# Supongamos que del PASO 2 (Baterías) tu consumo era:
consumo_casa = 3500 # Wh/día (ej. Nevera + Luces + Laptop)

print(f"--- ☀️ Dimensionando para Los Roques (Rad: {radiacion_los_roques} kWh/m2) ---")

# Usamos un panel comercial común hoy en día (ej. Jinko o Canadian Solar 450W)
mi_generador = GeneradorSolar(potencia_panel_w=450)

resultado_solar = mi_generador.dimensionar_arreglo(consumo_casa, radiacion_los_roques)

print(f"Panel seleccionado: {mi_generador.potencia_panel}W")
print(f"Paneles Necesarios: {resultado_solar['numero_paneles']} unidades")
print(f"Potencia Instalada: {resultado_solar['potencia_total_kw']} kWp")
print(f"Generación Promedio: {resultado_solar['generacion_diaria_estimada_kwh']} kWh/día")

if resultado_solar['generacion_diaria_estimada_kwh'] * 1000 > consumo_casa:
    excedente = (resultado_solar['generacion_diaria_estimada_kwh'] * 1000) - consumo_casa
    print(f"✅ ¡Sistema Saludable! Generas un excedente de {excedente:.0f} Wh diarios para recargar baterías.")
else:
    print("⚠️ Alerta: El sistema está muy justo.")