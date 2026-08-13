// Assets/Scripts/Core/Logica/Foco/FocoDispatcher.cs
using ComunicacionRemota;   // ActualizacionFoco (namespace derivado por defecto de "package comunicacion_remota")
using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using Unity.Burst.Intrinsics;
using UnityEngine;

/// <summary>
/// Vacía en el hilo principal la cola de ActualizacionFoco que rellena
/// ComunicacionRemotaClient desde el hilo de streaming gRPC. Mismo patrón
/// que DigestionAccionesPendientes (ConcurrentQueue + Update()), pero
/// separado y tipado a ActualizacionFoco en vez de JObject genérico con
/// "peticion" — no tiene sentido reutilizar aquella clase porque el
/// contrato de datos es distinto (ver conversación previa sobre por qué
/// SuscribirseFoco no encaja en el bus de "peticion"+handlers).
///
/// Responsabilidad única: deserializar "representacion" a una lista de
/// ElementoInstancia y pasársela al ElementoPool. Los elementos_globales
/// (clima/ciclo lunar) se exponen aparte, sin tocarlos aquí, porque ya
/// se decidió que van por un pipeline visual independiente y aún no
/// implementado.
/// </summary>
public class FocoDispatcher : MonoBehaviour
{
    [SerializeField] FocoSettings settings;
    [SerializeField] PrefabRegistry prefabRegistry;
    [SerializeField] Transform contenedorElementos;

    ElementoPool pool;

    // Rellenada desde el hilo de streaming gRPC (ver ComunicacionRemotaClient).
    // Público solo para que ComunicacionRemotaClient pueda encolar; nada más
    // debería escribir aquí.
    public readonly ConcurrentQueue<ActualizacionFoco> Pendientes = new();

    // Última lista de elementos_globales recibida, para quien la necesite
    // (futuro manejador de clima/ciclo lunar). Se sustituye entera en cada
    // tick, no se acumula.
    public IReadOnlyList<LogicaMundo.ElementoGlobalState> UltimosElementosGlobales { get; private set; }
        = new List<LogicaMundo.ElementoGlobalState>();

    void Awake()
    {
        pool = new ElementoPool(prefabRegistry, settings, contenedorElementos);
    }

    void Update()
    {
        // Se procesan todos los pendientes acumulados desde el último frame.
        // En condiciones normales debería haber como mucho 1 (el push es
        // por tick de servidor, no más rápido que los frames de Unity),
        // pero no asumimos eso: si hubiera más de uno acumulado, solo el
        // último importa (snapshot completo, no delta), así que procesamos
        // todos pero el pool simplemente queda en el estado del último.
        while (Pendientes.TryDequeue(out var actualizacion))
            Procesar(actualizacion);
    }

    void Procesar(ActualizacionFoco actualizacion)
    {
        if (!actualizacion.Ok)
        {
            Debug.LogWarning($"[FocoDispatcher] ActualizacionFoco con error: {actualizacion.Error}");
            return;
        }

        long tick = actualizacion.TickActual;

        // "representacion" son bytes UTF8 de un JSON: {"modo": "...", "elementos": [...]}.
        var json = JObject.Parse(Encoding.UTF8.GetString(actualizacion.Representacion.ToByteArray()));
        var elementosJson = (JArray)json["elementos"];

        var elementos = new List<ElementoInstancia>(elementosJson.Count);
        foreach (var item in elementosJson)
            elementos.Add(ElementoInstancia.DesdeJson((JObject)item, tick));

        pool.AplicarSnapshot(elementos, tick);

        UltimosElementosGlobales = actualizacion.ElementosGlobales;
    }
}