using System;
using UnityEngine;

/// <summary>
/// Representación visual de un bot en la simulación.
/// Responsabilidad: existir en el mundo 2D, mostrar su sprite y notificar si es clicado.
/// No contiene lógica de simulación — eso vive en el servidor Python.
///
/// Vive en: Presentation/Ingame
/// </summary>
[RequireComponent(typeof(SpriteRenderer))]
[RequireComponent(typeof(Collider2D))]
public class BotVisual : MonoBehaviour
{
    /// <summary>Notifica al Presenter que este bot fue clicado.</summary>
    public event Action<DatosBot> OnClicado;

    private DatosBot _datos;
    private SpriteRenderer _spriteRenderer;

    // ── Unity ─────────────────────────────────────────────────────────────────

    private void Awake()
    {
        _spriteRenderer = GetComponent<SpriteRenderer>();
    }

    private void OnMouseDown()
    {
        if (_datos != null)
            OnClicado?.Invoke(_datos);
    }

    // ── API pública (llamada por IngamePresenter) ─────────────────────────────

    /// <summary>
    /// Actualiza el estado visual del bot con los datos recibidos del servidor.
    /// Llamar cada vez que Python envíe un update.
    /// </summary>
    public void Actualizar(DatosBot datos)
    {
        _datos = datos;
        _spriteRenderer.color = datos.EstaVivo ? Color.white : Color.gray;
    }

    /// <summary>Posiciona el bot en el mundo.</summary>
    public void EstablecerPosicion(Vector2 posicion)
    {
        transform.position = posicion;
    }
}