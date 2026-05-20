using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;

/// <summary>
/// Contrato del servicio de perfiles.
/// 
/// Los Presenters solo conocen esta interfaz, nunca la implementación.
/// Esto permite cambiar el almacenamiento (local → servidor) sin tocar
/// ninguna pantalla.
/// 
/// Vive en Services/.
/// </summary>
public interface IPerfilService : IService
{
    // ── Consultas ────────────────────────────────────────────────────────────

    /// <summary>Devuelve todos los perfiles guardados en local.</summary>
    Task<List<DatosPerfil>> ObtenerPerfilesAsync();

    /// <summary>Devuelve un perfil concreto por nombre. Null si no existe.</summary>
    DatosPerfil ObtenerPerfil(string nombre);

    /// <summary>Perfil activo en esta sesión. Null si no se ha seleccionado ninguno.</summary>
    DatosPerfil PerfilActivo { get; }

    // ── Acciones ─────────────────────────────────────────────────────────────

    /// <summary>Crea un perfil nuevo con nombre dado. False si el nombre ya existe.</summary>
    Task<bool> CrearPerfilAsync(string nombre);

    /// <summary>Marca el perfil como activo para esta sesión.</summary>
    void EstablecerPerfilActivo(DatosPerfil perfil);

    /// <summary>
    /// Actualiza el tiempo jugado del perfil activo.
    /// El estado del juego lo persiste el servidor Python por su cuenta.
    /// Llamar al pausar o salir del Ingame.
    /// </summary>
    Task GuardarTiempoAsync(float tiempoJugadoSegundos);

    /// <summary>Elimina un perfil por nombre.</summary>
    Task<bool> EliminarPerfilAsync(string nombre);

    void ProcesarRespuesta(JObject mensaje);
}