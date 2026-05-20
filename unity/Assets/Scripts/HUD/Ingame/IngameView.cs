using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// View del HUD durante la simulación.
///
/// Layout:
///   Esquina superior izquierda — botones Opciones, Velocidad+, Velocidad-
///   Esquina inferior izquierda — botón Pausa
///   Lateral derecho            — overlay contextual (se muestra al clicar un elemento)
///   Centro                     — panel de opciones (volver al menú, etc.)
/// </summary>
public class IngameView : MonoBehaviour
{
    // ── Eventos que el Presenter escucha ─────────────────────────────────────
    public event Action OnOpciones;
    public event Action OnVelocidadAumentar;
    public event Action OnVelocidadDisminuir;
    public event Action OnPausa;
    public event Action OnVolverAlMenu;          // desde panel opciones
    public event Action<ElementoMundo> OnElementoClicado;       // agregado de todos los elementos
    public event Action OnTick;                  // pulso de polling

    // ── Referencias UI (asignar en Inspector) ────────────────────────────────
    [Header("Esquina superior izquierda")]
    [SerializeField] private Button btnOpciones;
    [SerializeField] private Button btnVelocidadMas;
    [SerializeField] private Button btnVelocidadMenos;
    [SerializeField] private TMP_Text textoVelocidad;

    [Header("Esquina inferior izquierda")]
    [SerializeField] private Button btnPausa;
    [SerializeField] private TMP_Text textoPausa;

    [Header("Overlay lateral derecho")]
    [SerializeField] private Transform contenedorOverlays;

    [Header("Panel opciones ingame")]
    [SerializeField] private GameObject panelOpciones;
    [SerializeField] private Button btnVolverAlMenu;
    [SerializeField] private Button btnCerrarOpciones;

    [Header("Bots")]
    [SerializeField] private GameObject prefabBot;
    [SerializeField] private Transform contenedorBots;

    // ── Estado interno ────────────────────────────────────────────────────────
    private Dictionary<Type, OverlayBase> _overlays = new();
    private Dictionary<int, BotVisual> _bots = new();   // id → visual
    private OverlayBase _overlayActivo;
    private Coroutine _pollingCoroutine;

    // ── Unity ─────────────────────────────────────────────────────────────────

    private void Awake()
    {
        btnOpciones.onClick.AddListener(() => OnOpciones?.Invoke());
        btnVelocidadMas.onClick.AddListener(() => OnVelocidadAumentar?.Invoke());
        btnVelocidadMenos.onClick.AddListener(() => OnVelocidadDisminuir?.Invoke());
        btnPausa.onClick.AddListener(() => OnPausa?.Invoke());
        btnVolverAlMenu.onClick.AddListener(() => OnVolverAlMenu?.Invoke());
        btnCerrarOpciones.onClick.AddListener(MostrarPanelOpciones);

        RegistrarOverlays();
        panelOpciones.SetActive(false);
    }

    // ── API que el Presenter usa ──────────────────────────────────────────────

    /// <summary>Inicia el pulso de polling cada <paramref name="intervalo"/> segundos.</summary>
    public void IniciarPolling(float intervalo)
    {
        if (_pollingCoroutine != null) StopCoroutine(_pollingCoroutine);
        _pollingCoroutine = StartCoroutine(CorrutinaPolling(intervalo));
    }

    public void DetenerPolling()
    {
        if (_pollingCoroutine != null) StopCoroutine(_pollingCoroutine);
    }

    /// <summary>Crea o actualiza el visual de un bot.</summary>
    public void ActualizarBot(DatosBot datos, Vector2 posicion)
    {
        if (!_bots.TryGetValue(datos.Id, out var bot))
        {
            var go = Instantiate(prefabBot, contenedorBots);
            bot = go.GetComponent<BotVisual>();
            bot.OnClicado += elemento => OnElementoClicado?.Invoke(elemento);
            _bots[datos.Id] = bot;
        }

        bot.Actualizar(datos);
        bot.EstablecerPosicion(posicion);
    }

    /// <summary>Elimina bots que ya no están en la simulación.</summary>
    public void EliminarBots(IEnumerable<int> ids)
    {
        foreach (var id in ids)
        {
            if (_bots.TryGetValue(id, out var bot))
            {
                Destroy(bot.gameObject);
                _bots.Remove(id);
            }
        }
    }

    /// <summary>Devuelve los IDs de los bots actualmente visibles en cámara.</summary>
    public List<int> ObtenerIdsVisibles()
    {
        var cam = Camera.main;
        var ids = new List<int>();
        var planes = GeometryUtility.CalculateFrustumPlanes(cam);

        foreach (var (id, bot) in _bots)
        {
            var bounds = bot.GetComponent<Renderer>().bounds;
            if (GeometryUtility.TestPlanesAABB(planes, bounds))
                ids.Add(id);
        }

        return ids;
    }

    public void MostrarOverlay(ElementoMundo elemento)
    {
        _overlayActivo?.Ocultar();

        if (_overlays.TryGetValue(elemento.GetType(), out var overlay))
        {
            overlay.Mostrar(elemento);
            _overlayActivo = overlay;
        }
        else
        {
            Debug.LogWarning($"[IngameView] No hay overlay para {elemento.GetType().Name}.");
        }
    }

    public void OcultarOverlay()
    {
        _overlayActivo?.Ocultar();
        _overlayActivo = null;
    }

    public void ActualizarVelocidad(float multiplicador)
    {
        textoVelocidad.text = $"x{multiplicador:F1}";
    }

    public void ActualizarEstadoPausa(bool pausado)
    {
        textoPausa.text = pausado ? "Reanudar" : "Pausa";
    }

    public void MostrarPanelOpciones()
    {
        panelOpciones.SetActive(!panelOpciones.activeSelf);
    }

    // ── Privados ──────────────────────────────────────────────────────────────

    private IEnumerator CorrutinaPolling(float intervalo)
    {
        while (true)
        {
            yield return new WaitForSeconds(intervalo);
            OnTick?.Invoke();
        }
    }

    private void RegistrarOverlays()
    {
        foreach (var overlay in contenedorOverlays.GetComponentsInChildren<OverlayBase>(true))
        {
            _overlays[overlay.TipoElemento] = overlay;
            overlay.Ocultar();
        }
    }
}