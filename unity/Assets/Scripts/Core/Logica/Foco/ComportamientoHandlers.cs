// Assets/Scripts/Core/Logica/Foco/ComportamientoHandlers.cs
using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// Registro extensible de "qué hacer visualmente cuando un elemento tiene
/// tal comportamiento". Cada entrada del diccionario sabe leer SOLO su
/// propia clave de "comportamientos" (ej. "Color") e ignora el resto.
///
/// Por qué así: el conjunto de comportamientos (Peso, Enterrable, Sonoro,
/// Termico, ...) es abierto y lo decide el simulador Python, no Unity.
/// Si tratáramos esto con un switch/if gigante habría que tocar esta clase
/// cada vez que aparece un comportamiento nuevo, y encima fallaría si el
/// tipo de dato cambia. Con este patrón, un comportamiento sin handler
/// simplemente no se pinta — no rompe nada — hasta que decidamos darle
/// tratamiento visual explícito.
///
/// De momento solo se implementa "Color" como ejemplo funcional; el resto
/// (Destruible, Sonoro, etc.) se añaden aquí mismo cuando toque diseñar
/// su representación visual concreta.
/// </summary>
public static class ComportamientoHandlers
{
    // Cada handler recibe la ElementoView (para tocar el GameObject) y el
    // JObject correspondiente a SU comportamiento (no el diccionario entero).
    static readonly Dictionary<string, Action<ElementoView, JObject>> handlers = new()
    {
        { "Color", AplicarColor },
        // { "Destruible", AplicarDestruible },  // pendiente de diseño visual
        // { "Sonoro", AplicarSonoro },          // pendiente: requiere tabla id_sonido -> AudioClip
    };

    /// <summary>
    /// Recorre el diccionario "comportamientos" del elemento y llama al
    /// handler registrado para cada clave presente. Las claves sin handler
    /// se ignoran silenciosamente (no es un error, es un comportamiento
    /// que aún no tiene tratamiento visual).
    /// </summary>
    public static void AplicarTodos(ElementoView view, JObject comportamientos)
    {
        if (comportamientos == null) return;

        foreach (var propiedad in comportamientos.Properties())
        {
            if (handlers.TryGetValue(propiedad.Name, out var handler))
                handler(view, (JObject)propiedad.Value);
        }
    }

    // ── Handlers concretos ───────────────────────────────────────────────

    /// <summary>
    /// Ejemplo: "Color": {"rgb_base": [...], "rgb_actual": [...], ...}
    /// Usamos rgb_actual porque, a diferencia de rgb_base, ya refleja
    /// modificadores aplicados (ej. tinte por temperatura, si existiera).
    /// </summary>
    static void AplicarColor(ElementoView view, JObject datosColor)
    {
        var rgb = datosColor["rgb_actual"];
        if (rgb == null) return;

        var color = new Color(
            (float)rgb[0],
            (float)rgb[1],
            (float)rgb[2]
        );

        var renderer = view.GetComponent<SpriteRenderer>();
        if (renderer != null)
            renderer.color = color;
    }
}