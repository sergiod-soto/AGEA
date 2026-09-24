# bioma.py


from dataclasses import dataclass

@dataclass(frozen=True)
class Bioma:
    
  
    nombre: str
    
    # Termodinámica
    tasa_conversion_radiacion_calor: float
    inercia_termica: float
    albedo: float                        # Factor [0.0 - 1.0] de reflexión solar
    
    # Hidrología / Atmósfera
    tasa_evaporacion_base: float        # Aporte base de vegetación/suelo a Humedad_Absoluta
    capacidad_retencion_humedad: float   # Límite o freno de saturación
    
    # Aerodinámica
    resistencia_viento: float           # Rugosidad del terreno / rozamiento