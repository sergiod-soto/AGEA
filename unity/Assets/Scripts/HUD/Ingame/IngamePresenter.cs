using System.Collections.Generic;
using Newtonsoft.Json.Linq;

/// <summary>
/// Presenter del Ingame.
///
/// Responsabilidades:
///   - Iniciar el polling y procesar cada respuesta de Python
///   - Gestionar velocidad y pausa enviando peticiones al servidor
///   - Delegar la actualización visual a IngameView
///   - Gestionar el overlay contextual al clicar un elemento
///   - Navegar de vuelta al menú principal
/// </summary>
public class IngamePresenter : PresenterBase
{
    private readonly IngameView _view;
    private readonly IConexionMundo _conexion;
    private readonly IPerfilService _perfilService;

    // ── Configuración ─────────────────────────────────────────────────────────
    private const float INTERVALO_POLLING = 0.1f;   // segundos entre cada petición
    private const float VELOCIDAD_INICIAL = 1f;
    private const float PASO_VELOCIDAD = 0.5f;
    private const float VELOCIDAD_MIN = 0.5f;
    private const float VELOCIDAD_MAX = 5f;

    // ── Estado ────────────────────────────────────────────────────────────────
    private float _velocidadActual = VELOCIDAD_INICIAL;
    private bool _pausado = false;
    private float _tiempoSesion = 0f;            // segundos jugados en esta sesión

    public IngamePresenter(IngameView view, ScreenManager navigator)
        : base(navigator)
    {
        _view = view;
        _conexion = ServiceLocator.Instance.Get<IConexionMundo>();
        _perfilService = ServiceLocator.Instance.Get<IPerfilService>();
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
    /// </summary>
    private void HandleTick()
    {
        if (_pausado) return;

        _tiempoSesion += INTERVALO_POLLING;

        var ids = _view.ObtenerIdsVisibles();
        var mensaje = new JObject
        {
            ["tipo"] = "simulacion",
            ["accion"] = "actualizar",
            ["elementos"] = new JArray(ids)
        };

        _conexion.EnviarMensaje(mensaje.ToString());

        // La respuesta llega de forma asíncrona a través de
        // IProcesamientoEntradaConexion, que debe llamar a ProcesarActualizacion()
    }

    /// <summary>
    /// Llamado por IProcesamientoEntradaConexion cuando llega
    /// un mensaje con "tipo": "simulacion" y "accion": "actualizar".
    /// </summary>
    public void ProcesarActualizacion(JObject mensaje)
    {
        var bots = mensaje["bots"]?.ToObject<List<DatosActualizacionBot>>();
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

    private void HandleVelocidadAumentar()
    {
        _velocidadActual = UnityEngine.Mathf.Min(_velocidadActual + PASO_VELOCIDAD, VELOCIDAD_MAX);
        EnviarVelocidad();
    }

    private void HandleVelocidadDisminuir()
    {
        _velocidadActual = UnityEngine.Mathf.Max(_velocidadActual - PASO_VELOCIDAD, VELOCIDAD_MIN);
        EnviarVelocidad();
    }

    private void HandlePausa()
    {
        _pausado = !_pausado;
        _view.ActualizarEstadoPausa(_pausado);

        _conexion.EnviarMensaje(new JObject
        {
            ["tipo"] = "simulacion",
            ["accion"] = _pausado ? "pausar" : "reanudar"
        }.ToString());
    }

    private void HandleOpciones()
    {
        _view.MostrarPanelOpciones();
    }

    private void HandleElementoClicado(ElementoMundo elemento)
    {
        _view.MostrarOverlay(elemento);
    }

    private async void HandleVolverAlMenu()
    {
        await _perfilService.GuardarTiempoAsync(_tiempoSesion);
        Navigator.NavigateTo(ScreenManager.Screen.MenuPrincipal);
    }

    // ── Privados ──────────────────────────────────────────────────────────────

    private void EnviarVelocidad()
    {
        _view.ActualizarVelocidad(_velocidadActual);

        _conexion.EnviarMensaje(new JObject
        {
            ["tipo"] = "simulacion",
            ["accion"] = "velocidad",
            ["velocidad"] = _velocidadActual
        }.ToString());
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