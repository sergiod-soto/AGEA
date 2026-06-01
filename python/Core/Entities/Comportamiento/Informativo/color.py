from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Color(Comportamiento):
    """
    Color del Elemento en RGB

    Parametros:

    - rgb_base: tuple[float, float, float]
    - transparente: float = 0

    Metodos abstractos:

    -
    """

    def __init__(
        self, rgb_base: tuple[float, float, float], transparente: float = 0, **kwargs
    ):
        super().__init__(**kwargs)
        self.rgb_base = rgb_base  # color base: proporcion, inmutable
        self.transparente = transparente  # % de tansparencia
        self.rgb_actual = rgb_base  # color que refleja
        self.intensidad = 0  # intensidad del color reflejado

    def iluminar_con_color(
        self, color_luz: tuple[float, float, float], intensidad_entrante: float
    ):
        """
        Modifica el color (e intensidad) que refleja
        el elemento en base al color e intensidad con el que es iluminado
        """
        r_actual, g_actual, b_actual = self.rgb_actual
        r_entrante, g_entrante, b_entrante = color_luz

        intensidad_base = self.intensidad

        # proporcion del color * intensidad
        r_actual *= intensidad_base
        g_actual *= intensidad_base
        b_actual *= intensidad_base

        r_entrante *= intensidad_entrante
        g_entrante *= intensidad_entrante
        b_entrante *= intensidad_entrante

        max_rgb = 0
        r_temp = r_actual + r_entrante
        g_temp = g_actual + g_entrante
        b_temp = b_actual + b_entrante

        if r_temp > max_rgb:
            max_rgb = r_temp

        if g_temp > max_rgb:
            max_rgb = g_temp

        if b_temp > max_rgb:
            max_rgb = b_temp

        r_temp = r_temp / max_rgb * 255  # normalizo
        g_temp = g_temp / max_rgb * 255
        b_temp = b_temp / max_rgb * 255

        self.rgb_actual = (r_temp, g_temp, b_temp)
        self.intensidad += intensidad_entrante
