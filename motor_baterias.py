import math

class CargaCritica:
    def __init__(self):
        self.equipos = [] # Lista para guardar los electrodomésticos

    def agregar_equipo(self, nombre, potencia_watts, cantidad, horas_uso_diario):
        """
        Agrega un equipo al perfil de carga crítica.
        """
        consumo_individual = potencia_watts * horas_uso_diario
        consumo_total_equipo = consumo_individual * cantidad
        
        equipo = {
            "nombre": nombre,
            "potencia_w": potencia_watts,
            "cantidad": cantidad,
            "horas": horas_uso_diario,
            "wh_dia": consumo_total_equipo
        }
        self.equipos.append(equipo)
        print(f"✅ Agregado: {cantidad}x {nombre} ({consumo_total_equipo} Wh/día)")

    def obtener_consumo_total_diario(self):
        total_wh = sum(e['wh_dia'] for e in self.equipos)
        return total_wh

    def obtener_potencia_pico(self):
        # Asumimos el peor caso: todo se prende a la vez (para el inversor más adelante)
        total_watts = sum(e['potencia_w'] * e['cantidad'] for e in self.equipos)
        return total_watts

class BancoBaterias:
    def __init__(self, voltaje_sistema=24, tipo="Litio"):
        self.voltaje = voltaje_sistema
        self.tipo = tipo
        
        # Profundidad de descarga recomendada (DoD)
        # Litio (LiFePO4) aguanta hasta 80% (0.8) o 90%
        # Plomo-Ácido (GEL/AGM) no se recomienda bajar del 50% (0.5)
        if tipo == "Litio":
            self.dod = 0.9 
        else:
            self.dod = 0.5 

    def dimensionar(self, consumo_diario_wh, dias_autonomia):
        """
        Calcula la capacidad necesaria del banco.
        Fórmula: Capacidad = (Energía * Días) / (Voltaje * DoD)
        """
        energia_requerida_wh = consumo_diario_wh * dias_autonomia
        
        # Capacidad en Amperios-Hora (Ah)
        capacidad_ah_total = energia_requerida_wh / (self.voltaje * self.dod)
        
        return {
            "energia_reserva_kwh": energia_requerida_wh / 1000,
            "capacidad_banco_ah": round(capacidad_ah_total, 2),
            "voltaje_sistema": self.voltaje,
            "tipo_bateria": self.tipo
        }

# --- SIMULACIÓN: Caso "Apartamento en Caracas con fallas frecuentes" ---

# 1. Definimos las cargas críticas (Lo que quiero prendido cuando se va la luz)
mi_casa = CargaCritica()
print("--- 🏠 Definición de Cargas ---")
mi_casa.agregar_equipo("Nevera/Heladera", 300, 1, 24)      # 150W todo el día (ciclos)
mi_casa.agregar_equipo("Aire Acondicionado", 1000, 2, 8)      # 150W todo el día (ciclos)
# mi_casa.agregar_equipo("Nevera/Heladera", 150, 1, 24)      # 150W todo el día (ciclos)
mi_casa.agregar_equipo("Bombillos LED", 25, 6, 6)           # 6 bombillos por 6 horas
mi_casa.agregar_equipo("Router WiFi", 15, 1, 24)           # Internet no puede faltar
mi_casa.agregar_equipo("Laptop", 65, 1, 16)                 # Cargar laptop 4 horas
# mi_casa.agregar_equipo("Ventilador", 60, 2, 8)             # 2 ventiladores para dormir

consumo_total = mi_casa.obtener_consumo_total_diario()
print(f"\n⚡ Consumo Crítico Diario: {consumo_total} Wh/día")

# 2. Dimensionamos las baterías
# Escenario: Quiero que el sistema aguante 1.5 días (36 horas) sin nada de sol ni red.
print("\n--- 🔋 Dimensionamiento del Banco ---")
bateria_litio = BancoBaterias(voltaje_sistema=24, tipo="Litio")
resultado = bateria_litio.dimensionar(consumo_diario_wh=consumo_total, dias_autonomia=1.5)

print(f"Para tener 1 días de autonomía en Litio a 24V necesitas:")
print(f"Capacidad Total: {resultado['capacidad_banco_ah']} Ah")
print(f"Energía Real Almacenada: {resultado['energia_reserva_kwh']} kWh")

# 3. Inventory Matcher Básico (Adelanto Fase 2)
# Supongamos que compramos baterías Pylontech de 24V 100Ah
capacidad_modulo_comercial = 100 # Ah
modulos_necesarios = math.ceil(resultado['capacidad_banco_ah'] / capacidad_modulo_comercial)

print(f"\n🛒 LISTA DE COMPRA SUGERIDA:")
print(f"Necesitas {modulos_necesarios} baterías de {capacidad_modulo_comercial}Ah en paralelo.")