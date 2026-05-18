using UnityEngine;

/// <summary>
/// Clase base para todos los Presenters.
/// 
/// Ciclo de vida:
///   1. ScreenManager instancia el Presenter (constructor recibe View + ScreenManager)
///   2. ScreenManager llama a Initialize() -> el Presenter se suscribe a eventos de la View
///   3. ScreenManager llama a Dispose() al navegar fuera -> el Presenter se desuscribe
/// </summary>
public abstract class PresenterBase
{
    protected readonly ScreenManager Navigator;

    protected PresenterBase(ScreenManager navigator)
    {
        Navigator = navigator;
    }

    /// <summary>
    /// Se llama justo despues de que la View es activada.
    /// Aqui se suscriben eventos y se carga el estado inicial.
    /// </summary>
    public abstract void Initialize();

    /// <summary>
    /// Se llama antes de navegar a otra pantalla.
    /// Aqui se desuscriben todos los eventos para evitar memory leaks.
    /// </summary>
    public abstract void Dispose();
}