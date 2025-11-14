"""
.       Datos del mundo generado/cargado
"""

"""
        Bots
"""
# region
bots = {}  # K: id, V: bot


def serializar_bots():
    return [b.serialize() if hasattr(b, "serialize") else b for b in bots.values()]


# endregion


"""
        Biomas
"""
# region


"""
        Desierto
"""
# region


# endregion

"""
        Mar
"""
# region


# endregion

"""
        Montaña
"""
# region


# endregion

"""
        Pradera
"""
# region


# endregion

"""
        Tundra
"""
# region


# endregion


# endregion
