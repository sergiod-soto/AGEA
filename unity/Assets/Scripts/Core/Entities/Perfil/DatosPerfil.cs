using System;

/// <summary>
/// Modelo de datos de un perfil de usuario.
/// C# puro, sin dependencias de Unity.
///
/// El estado del juego (bots, elementos del mundo, comportamientos)
/// vive enteramente en el servidor Python. Unity solo conoce
/// los metadatos del perfil necesarios para la UI.
///
/// Vive en: Core/Entities
/// </summary>
[Serializable]
public class DatosPerfil
{
    public string Nombre { get; set; }
    public float TiempoTotalJuego { get; set; }   // en segundos
    public int NumeroDeBots { get; set; }

    /// <summary>
    /// Un perfil tiene datos si tiene al menos un bot creado.
    /// Lo usa la View para decidir si el botón de carga es interactuable.
    /// </summary>
    public bool TieneDatos => NumeroDeBots > 0;

    /// <summary>Tiempo formateado para mostrar en UI (ej: "2h 14m", "45m").</summary>
    public string TiempoFormateado
    {
        get
        {
            var span = TimeSpan.FromSeconds(TiempoTotalJuego);
            return span.Hours > 0
                ? $"{span.Hours}h {span.Minutes}m"
                : $"{span.Minutes}m";
        }
    }

    public static DatosPerfil Nuevo(string nombre) => new DatosPerfil
    {
        Nombre = nombre,
        TiempoTotalJuego = 0f,
        NumeroDeBots = 0
    };
}
