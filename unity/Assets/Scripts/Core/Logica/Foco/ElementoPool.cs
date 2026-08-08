// Assets/Scripts/Core/Logica/Foco/ElementoPool.cs
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Gestiona el ciclo de vida de los GameObjects que representan elementos
/// del mundo (Bot, Piedra, cualquier tipo). Sustituye a IBotsLogica,
/// BotsDatos y DatosMundo: es la única fuente de verdad de "qué elemento
/// tiene qué GameObject" para todo el juego, no solo para bots.
///
/// Estrategia (decidida explícitamente, no asumida):
/// - Cada ActualizacionFoco trae el snapshot COMPLETO de la región (no deltas).
/// - En cada snapshot: los elementos presentes se crean (si no existían) o
///   se actualizan (si ya existían); NO se reconstruye todo desde cero.
/// - Un elemento que lleva más de TicksGraciaAntesDeDestruir ticks sin
///   aparecer en ningún snapshot se destruye. El margen de gracia es para
///   tolerar que la cámara se aleje y vuelva sin recrear todo de golpe.
/// </summary>
public class ElementoPool
{
    readonly PrefabRegistry prefabRegistry;
    readonly CoordinateMapper mapper;
    readonly int ticksGracia;
    readonly Transform contenedor;

    // Clave: id_elemento. Es el único índice que necesita el pool.
    readonly Dictionary<int, ElementoView> instancias = new();

    public ElementoPool(PrefabRegistry prefabRegistry, FocoSettings settings, Transform contenedor)
    {
        this.prefabRegistry = prefabRegistry;
        this.mapper = new CoordinateMapper(settings);
        this.ticksGracia = settings.TicksGraciaAntesDeDestruir;
        this.contenedor = contenedor;
    }

    /// <summary>
    /// Punto de entrada único: se llama una vez por cada ActualizacionFoco
    /// recibido (ya en el hilo principal, vía FocoDispatcher).
    /// </summary>
    public void AplicarSnapshot(List<ElementoInstancia> elementos, long tickActual)
    {
        // 1. Crear o actualizar cada elemento presente en este snapshot.
        foreach (var datos in elementos)
        {
            if (instancias.TryGetValue(datos.IdElemento, out var view))
            {
                // Ya existe: solo actualizar (reutiliza el GameObject).
                view.Actualizar(datos, mapper);
            }
            else
            {
                // Nuevo: crear e instanciar desde el registro de prefabs.
                view = CrearInstancia(datos);
                if (view == null) continue; // sin prefab registrado para esta clase, se ignora

                view.Inicializar(datos);
                view.Actualizar(datos, mapper);
                instancias[datos.IdElemento] = view;
            }
        }

        // 2. Destruir los que llevan demasiados ticks sin aparecer.
        //    Se recorre sobre una copia de las claves porque vamos a
        //    modificar el diccionario dentro del bucle.
        var idsAEliminar = new List<int>();
        foreach (var kvp in instancias)
        {
            long ticksAusente = tickActual - kvp.Value.Datos.UltimoTickVisto;
            if (ticksAusente > ticksGracia)
                idsAEliminar.Add(kvp.Key);
        }

        foreach (var id in idsAEliminar)
        {
            if (instancias.TryGetValue(id, out var view) && view != null)
                Object.Destroy(view.gameObject);
            instancias.Remove(id);
        }
    }

    ElementoView CrearInstancia(ElementoInstancia datos)
    {
        var prefab = prefabRegistry.ObtenerPrefab(datos.Clase);
        if (prefab == null) return null;

        var go = Object.Instantiate(prefab, contenedor);
        var view = go.GetComponent<ElementoView>();

        if (view == null)
        {
            Debug.LogError($"[ElementoPool] El prefab de '{datos.Clase}' no tiene componente ElementoView.");
            Object.Destroy(go);
            return null;
        }

        return view;
    }

    /// <summary>Destruye todas las instancias activas. Útil al desconectar o cambiar de escena.</summary>
    public void LimpiarTodo()
    {
        foreach (var view in instancias.Values)
            if (view != null) Object.Destroy(view.gameObject);
        instancias.Clear();
    }
}