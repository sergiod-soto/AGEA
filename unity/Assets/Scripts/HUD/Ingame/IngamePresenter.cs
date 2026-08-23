// Assets/Scripts/HUD/Ingame/IngamePresenter.cs
using System.Collections.Generic;
using System.Threading.Tasks;
using ComunicacionRemota;
using Newtonsoft.Json.Linq;

/// <summary>
/// Presenter del Ingame.
///
/// Responsabilidades:
///   - Iniciar el polling y procesar cada respuesta de Python (vía gRPC)
///   - Gestionar velocidad y pausa enviando peticiones al servidor
///   - Delegar la actualización visual a IngameView
///   - Gestionar el overlay contextual al clicar un elemento
///   - Navegar de vuelta al menú principal
/// </summary>
public class IngamePresenter : PresenterBase
{
    private readonly IngameView _view;
    private readonly IConexionMundo _conexion;

    // ── Configuración ─────────────────────────────────────────────────────────
    private const float INTERVALO_POLLING = 0.1f;   // segundos entre cada petición
    private const float VELOCIDAD_INICIAL = 1f;
    private const float PASO_VELOCIDAD = 0.5f;
    private const float VELOCIDAD_MIN = 0.5f;
    private const float VELOCIDAD_MAX = 5f;

    // TODO(decisión pendiente): confirmar a qué ComponenteDestino va cada operación.
    // Ver pregunta al usuario en la respuesta del chat.
    private const ComponenteDestino COMPONENTE_BOTS = ComponenteDestino.GestorBots;
    private const ComponenteDestino COMPONENTE_SIMULACION = ComponenteDestino.GestorMundo;

    // ── Estado ────────────────────────────────────────────────────────────────
    private float _velocidadActual = VELOCIDAD_INICIAL;
    private bool _pausado = false;
    private float _tiempoSesion = 0f;            // segundos jugados en esta sesión

    // Evita que se solapen peticiones "actualizar" si la respuesta tarda más
    // que INTERVALO_POLLING: sin esta guarda, con latencia de red variable
    // podrían quedar varias peticiones en vuelo a la vez y llegar desordenadas,
    // pintando un estado viejo encima de uno más nuevo.
    private bool _actualizando = false;

    public IngamePresenter(IngameView view, ScreenManager navigator)
        : base(navigator)
    {
        _view = view;
        _conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    // ── Ciclo de vida ─────────────────────────────────────────────────────────

    public override void Initialize()
    {
        _view.OnTick += HandleTick;
        _view.OnVelocidadAumentar += HandleVelocidadAumentar;
        _view.OnVelocidadDisminuir += HandleVelocidadDisminuir;
        _view.OnPausa += HandlePausa;
        _view.OnOpciones += HandleOpciones;
        _view.OnVolverAlMenu += HandleVolverAlMenu;
        _view.OnElementoClicado += HandleElementoClicado;

        _view.ActualizarVelocidad(_velocidadActual);
        _view.ActualizarEstadoPausa(_pausado);
        _view.IniciarPolling(INTERVALO_POLLING);
    }

    public override void Dispose()
    {
        _view.OnTick -= HandleTick;
        _view.OnVelocidadAumentar -= HandleVelocidadAumentar;
        _view.OnVelocidadDisminuir -= HandleVelocidadDisminuir;
        _view.OnPausa -= HandlePausa;
        _view.OnOpciones -= HandleOpciones;
        _view.OnVolverAlMenu -= HandleVolverAlMenu;
        _view.OnElementoClicado -= HandleElementoClicado;

        _view.DetenerPolling();
    }

    // ── Handlers ─────────────────────────────────────────────────────────────

    /// <summary>
    /// Cada tick: pide a Python los datos de los elementos visibles
    /// y actualiza los visuals con la respuesta.
    /// "async void" porque es un manejador de evento (OnTick no admite Task);
    /// las excepciones dentro se capturan igualmente porque EnviarMensaje
    /// nunca lanza (ver ConexionMundoManager: los fallos de red se devuelven
    /// como EjecutarResultado.ok = false, no como excepción).
    /// </summary>
    private async void HandleTick()
    {
        if (_pausado) return;
        if (_actualizando) return; // petición anterior todavía en vuelo: se descarta este tick

        _tiempoSesion += INTERVALO_POLLING;
        _actualizando = true;

        try
        {
            var ids = _view.ObtenerIdsVisibles();
            var payload = new JObject
            {
                ["elementos"] = new JArray(ids)
            };

            EjecutarResultado resultado = await _conexion.EnviarMensaje(
                COMPONENTE_BOTS, "actualizar", payload);

            if (!resultado.ok)
            {
                UnityEngine.Debug.LogWarning($"[IngamePresenter] Fallo al actualizar: {resultado.error}");
                return;
            }

            AplicarActualizacion(resultado.payload);
        }
        finally
        {
            _actualizando = false;
        }
    }

    /// <summary>
    /// Parsea el payload de la respuesta "actualizar" y actualiza los visuals.
    /// </summary>
    private void AplicarActualizacion(JObject payload)
    {
        var bots = payload?["bots"]?.ToObject<List<DatosActualizacionBot>>();
        if (bots == null) return;

        foreach (var bot in bots)
        {
            _view.ActualizarBot(
                new DatosBot
                {
                    Id = bot.Id,
                    Generacion = bot.Generacion,
                    EstaVivo = bot.EstaVivo
                },
                new UnityEngine.Vector2(bot.X, bot.Y)
            );
        }
    }

    private async void HandleVelocidadAumentar()
    {
        _velocidadActual = UnityEngine.Mathf.Min(_velocidadActual + PASO_VELOCIDAD, VELOCIDAD_MAX);
        await EnviarVelocidad();
    }

    private async void HandleVelocidadDisminuir()
    {
        _velocidadActual = UnityEngine.Mathf.Max(_velocidadActual - PASO_VELOCIDAD, VELOCIDAD_MIN);
        await EnviarVelocidad();
    }

    private async void HandlePausa()
    {
        _pausado = !_pausado;
        _view.ActualizarEstadoPausa(_pausado);

        var resultado = await _conexion.EnviarMensaje(
            COMPONENTE_SIMULACION,
            _pausado ? "pausar" : "reanudar",
            new JObject());

        if (!resultado.ok)
        {
            UnityEngine.Debug.LogWarning($"[IngamePresenter] Fallo al {(_pausado ? "pausar" : "reanudar")}: {resultado.error}");
        }
    }

    private void HandleOpciones()
    {
        _view.MostrarPanelOpciones();
    }

    private void HandleVolverAlMenu()
    {
        // El overlay de opciones no navega por sí mismo (decisión acordada:
        // es local a Ingame); solo el Presenter tiene acceso al Navigator.
        Navigator.NavigateTo(ScreenManager.Screen.MenuPrincipal);
    }

    private void HandleElementoClicado(ElementoMundo elemento)
    {
        _view.MostrarOverlay(elemento);
    }

    // ── Privados ──────────────────────────────────────────────────────────────

    private async Task EnviarVelocidad()
    {
        _view.ActualizarVelocidad(_velocidadActual);

        var payload = new JObject { ["velocidad"] = _velocidadActual };
        var resultado = await _conexion.EnviarMensaje(COMPONENTE_SIMULACION, "velocidad", payload);

        if (!resultado.ok)
        {
            UnityEngine.Debug.LogWarning($"[IngamePresenter] Fallo al cambiar velocidad: {resultado.error}");
        }
    }
}

/// <summary>
/// DTO de la respuesta de Python para cada bot.
/// Solo existe para deserializar el JSON — no es un modelo de dominio.
/// </summary>
internal class DatosActualizacionBot
{
    public int Id { get; set; }
    public float X { get; set; }
    public float Y { get; set; }
    public float Fitness { get; set; }
    public int Generacion { get; set; }
    public bool EstaVivo { get; set; }
}