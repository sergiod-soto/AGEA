# Infraestructura/Gestores/Transporte/validar_dispatch.py
"""
Comprueba al arrancar que cada RPC declarado en el .proto tiene su módulo en el
registry del servicer. Sin esto, un RPC sin registrar solo falla (KeyError) la
primera vez que alguien lo llama, que puede ser horas después.
"""


def validar_dispatch(
    descriptor_servicio, dispatch: dict, excluir: frozenset = frozenset()
) -> None:
    """
    descriptor_servicio: p. ej. pb.DESCRIPTOR.services_by_name["LogicaMundoService"].
    excluir: RPC que el servicer atiende fuera del dispatch.
    """
    declarados = {m.name for m in descriptor_servicio.methods}
    sin_implementar = (declarados - excluir) - dispatch.keys()
    sobrantes = dispatch.keys() - declarados  # módulo registrado sin RPC en el proto
    if sin_implementar or sobrantes:
        raise RuntimeError(
            f"{descriptor_servicio.name}: RPC sin implementar {sorted(sin_implementar)}; "
            f"módulos sin RPC {sorted(sobrantes)}."
        )
