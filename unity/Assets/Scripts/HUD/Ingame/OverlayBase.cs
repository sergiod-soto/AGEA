using System;
using UnityEngine;

/// <summary>
/// Clase base para todos los overlays del Ingame.
///
/// Vive en: Presentation/Ingame
///
/// Para crear un nuevo overlay:
///   1. Crea una clase que herede de OverlayBase (ej: BotOverlay)
///   2. Implementa TipoElemento y Poblar()
///   3. Añade el GameObject con ese componente como hijo del panel de overlays
///   4. La IngameView lo detecta automáticamente — no hay que tocar nada más
///
/// Ejemplo:
///   public class BotOverlay : OverlayBase
///   {
///       public override Type TipoElemento => typeof(DatosBot);
///
///       protected override void Poblar(ElementoMundo elemento)
///       {
///           var datos = (DatosBot)elemento;
///           textoFitness.text = datos.Fitness.ToString("F2");
///       }
///   }
/// </summary>
public abstract class OverlayBase : MonoBehaviour
{
    /// <summary>
    /// Tipo de ElementoMundo que este overlay sabe mostrar.
    /// Usado por IngameView para encontrar el overlay correcto.
    /// </summary>
    public abstract Type TipoElemento { get; }

    /// <summary>Rellena el overlay con los datos del elemento.</summary>
    protected abstract void Poblar(ElementoMundo elemento);

    // ── API pública (llamada por IngameView) ──────────────────────────────────

    public void Mostrar(ElementoMundo elemento)
    {
        gameObject.SetActive(true);
        Poblar(elemento);
    }

    public void Ocultar()
    {
        gameObject.SetActive(false);
    }
}