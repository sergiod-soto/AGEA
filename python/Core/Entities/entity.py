from enum import Enum


class Modos(str, Enum):
    """
    Modos válidos para serializar/representar un Elemento o Comportamiento.

    Sustituye al parámetro modo: str, que aceptaba cualquier string y
    fallaba en silencio ante un typo: getattr(self, f"serialize_x_{modo}")
    simplemente no encontraba el hook específico y caía al genérico sin
    avisar. Con Enum, un valor inválido revienta en el momento de crearlo
    (Modos("guardaddo") -> ValueError), no varias líneas más abajo.

    Hereda también de str para no romper comparaciones existentes tipo
    modo == "guardado" mientras se migra el resto del código.
    """

    guardado = "guardado"
    transporte = "transporte"
    representacion = "representacion"