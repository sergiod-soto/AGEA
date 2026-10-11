// Assets/Scripts/Dev/FocoTestLogger.cs
using System.Text;
using ComunicacionRemota;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// Script de PRUEBA, no de producción: confirma en la Consola que el
/// servidor está respondiendo correctamente al stream de SuscribirseFoco
/// (tick, ok/error, cuántos elementos llegan). La confirmación VISUAL de
/// que el mundo se ve ya la da TraductorMundo pintando el Tilemap; este
/// script es el complemento para saber SI está llegando algo y en qué
/// estado, sin depender solo de "veo tiles en pantalla o no".
///
/// Uso: añadir este componente a cualquier GameObject de la escena de
/// prueba. No pertenece a ningún prefab final del juego.
/// </summary>
public class FocoTestLogger : MonoBehaviour
{
    private IFocoStream _receptor;
    private int _mensajesRecibidos;
    private float _tiempoUltimoMensaje;

    private void Awake()
    {
        // Awake (no OnEnable): mismo motivo que TraductorMundo -- ServiceLocator
        // corre a DefaultExecutionOrder -100, así que el registro ya existe aquí.
        _receptor = ServiceLocator.Instance.Get<IFocoStream>();
    }

    private void OnEnable() => _receptor.OnActualizacionRecibida += Procesar;
    private void OnDisable() => _receptor.OnActualizacionRecibida -= Procesar;

    private void Procesar(ActualizacionFoco actualizacion)
    {
        _mensajesRecibidos++;
        float delta = Time.realtimeSinceStartup - _tiempoUltimoMensaje;
        _tiempoUltimoMensaje = Time.realtimeSinceStartup;

        if (!actualizacion.Ok)
        {
            Debug.LogError($"[FocoTestLogger] #{_mensajesRecibidos} ERROR del servidor: {actualizacion.Error}");
            return;
        }

        // Reutilizamos el mismo parseo que TraductorMundo solo para contar
        // elementos en el log -- no tocamos el Tilemap desde aquí.
        //
        int numElementos = 0;
        if (!actualizacion.Representar.IsEmpty)
        {
            var json = JObject.Parse(Encoding.UTF8.GetString(actualizacion.Representar.ToByteArray()));
            numElementos = (json["elementos"] as JArray)?.Count ?? 0;
            Debug.Log($"[FocoTestLogger] #{_mensajesRecibidos} tick={actualizacion.TickActual} " +
                      $"elementos={numElementos} globales={actualizacion.ElementosGlobales.Count} " +
                      $"(+{delta:0.00}s desde el anterior)");
        }
    }
}