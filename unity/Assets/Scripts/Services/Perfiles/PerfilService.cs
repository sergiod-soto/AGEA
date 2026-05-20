using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// Implementación de IPerfilService que habla con el servidor Python vía TCP.
///
/// Protocolo de mensajes:
///   Request:  { "tipo": "perfil", "accion": "...", "id": "guid", "datos": { ... } }
///   Response: { "tipo": "perfil", "accion": "...", "id": "guid", "datos": { ... } }
///
/// El campo "id" es un GUID de correlación que permite saber
/// a qué petición pertenece cada respuesta.
///
/// IProcesamientoEntradaConexion debe llamar a ProcesarRespuesta()
/// cuando reciba un mensaje con "tipo": "perfil".
/// </summary>
public class PerfilService : MonoBehaviour, IPerfilService
{
    // ── Estado ────────────────────────────────────────────────────────────────

    public DatosPerfil PerfilActivo { get; private set; }

    /// <summary>
    /// Peticiones en vuelo: id → TaskCompletionSource esperando respuesta.
    /// </summary>
    private readonly Dictionary<string, TaskCompletionSource<JObject>> _pendientes = new();

    private IConexionMundo _conexion;

    // ── Unity ─────────────────────────────────────────────────────────────────

    private void Awake()
    {
        _conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    // ── IPerfilService ────────────────────────────────────────────────────────

    public async Task<List<DatosPerfil>> ObtenerPerfilesAsync()
    {
        var respuesta = await EnviarAsync("obtener_perfiles");
        if (respuesta == null) return new List<DatosPerfil>();

        return respuesta["datos"]?.ToObject<List<DatosPerfil>>()
               ?? new List<DatosPerfil>();
    }

    public DatosPerfil ObtenerPerfil(string nombre)
    {
        // Búsqueda síncrona en caché local si ya los tenemos cargados.
        // Para casos donde necesitamos ir al servidor, usar ObtenerPerfilesAsync primero.
        Debug.LogWarning("[PerfilService] ObtenerPerfil es síncrono. " +
                         "Asegúrate de haber llamado ObtenerPerfilesAsync antes.");

        Debug.LogWarning("No implementado");

        return null;
    }

    public async Task<bool> CrearPerfilAsync(string nombre)
    {
        var respuesta = await EnviarAsync("crear_perfil", new JObject
        {
            ["nombre"] = nombre
        });

        return respuesta?["exito"]?.Value<bool>() ?? false;
    }

    public void EstablecerPerfilActivo(DatosPerfil perfil)
    {
        PerfilActivo = perfil;
    }

    public async Task GuardarTiempoAsync(float tiempoJugadoSegundos)
    {
        if (PerfilActivo == null)
        {
            Debug.LogError("[PerfilService] No hay perfil activo. No se puede guardar.");
            return;
        }

        await EnviarAsync("guardar_tiempo", new JObject
        {
            ["nombre"] = PerfilActivo.Nombre,
            ["tiempoJugado"] = tiempoJugadoSegundos
        });
    }

    public async Task<bool> EliminarPerfilAsync(string nombre)
    {
        var respuesta = await EnviarAsync("eliminar_perfil", new JObject
        {
            ["nombre"] = nombre
        });

        return respuesta?["exito"]?.Value<bool>() ?? false;
    }

    // ── API para IProcesamientoEntradaConexion ────────────────────────────────

    /// <summary>
    /// Llamar desde IProcesamientoEntradaConexion cuando llegue
    /// un mensaje con "tipo": "perfil".
    /// Completa la Task que estaba esperando esa respuesta.
    /// </summary>
    public void ProcesarRespuesta(JObject mensaje)
    {
        var id = mensaje["id"]?.Value<string>();
        if (id == null) return;

        if (_pendientes.TryGetValue(id, out var tcs))
        {
            _pendientes.Remove(id);
            tcs.SetResult(mensaje);
        }
        else
        {
            Debug.LogWarning($"[PerfilService] Respuesta sin petición pendiente. id={id}");
        }
    }

    // ── Privados ──────────────────────────────────────────────────────────────

    /// <summary>
    /// Envía un mensaje al servidor Python y devuelve un Task
    /// que se completa cuando llega la respuesta con el mismo id.
    /// </summary>
    private Task<JObject> EnviarAsync(string accion, JObject datos = null)
    {
        var id = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<JObject>();

        _pendientes[id] = tcs;

        var mensaje = new JObject
        {
            ["tipo"] = "perfil",
            ["accion"] = accion,
            ["id"] = id,
            ["datos"] = datos ?? new JObject()
        };

        _conexion.EnviarMensaje(mensaje.ToString(Formatting.None));

        // Timeout: si Python no responde en 5s, la Task falla limpiamente
        _ = TimeoutAsync(id, tcs, segundos: 5);

        return tcs.Task;
    }

    private async Task TimeoutAsync(string id, TaskCompletionSource<JObject> tcs, int segundos)
    {
        await Task.Delay(TimeSpan.FromSeconds(segundos));

        if (_pendientes.Remove(id))
        {
            Debug.LogError($"[PerfilService] Timeout esperando respuesta de Python. id={id}");
            tcs.SetResult(null);
        }
    }


}