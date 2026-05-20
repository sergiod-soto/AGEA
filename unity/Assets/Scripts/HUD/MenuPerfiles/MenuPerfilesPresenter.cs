using System.Collections.Generic;

/// <summary>
/// Presenter de la pantalla de perfiles.
/// Responsabilidad ÚNICA: decidir qué ocurre cuando el usuario interactúa.
/// No toca UI directamente. Solo llama a métodos de la View y a servicios.
/// Es C# puro: sin MonoBehaviour, sin Unity, testeable de forma aislada.
/// </summary>
public class MenuPerfilesPresenter : PresenterBase
{
    private readonly MenuPerfilesView _view;
    private readonly IPerfilService _perfilService;

    public MenuPerfilesPresenter(MenuPerfilesView view, ScreenManager navigator)
        : base(navigator)
    {
        _view = view;
        _perfilService = ServiceLocator.Instance.Get<IPerfilService>();
    }

    // ── Ciclo de vida (llamado por ScreenManager) ─────────────────────────────

    public override void Initialize()
    {
        // Suscribir eventos
        _view.OnVolver += HandleVolver;
        _view.OnSeleccionarPerfil += HandleSeleccionarPerfil;
        _view.OnConfirmarCreacion += HandleConfirmarCreacion;

        // Cargar estado inicial
        CargarPerfiles();
    }

    public override void Dispose()
    {
        // Desuscribir siempre para evitar memory leaks
        _view.OnVolver -= HandleVolver;
        _view.OnSeleccionarPerfil -= HandleSeleccionarPerfil;
        _view.OnConfirmarCreacion -= HandleConfirmarCreacion;
    }

    // ── Handlers ─────────────────────────────────────────────────────────────

    private async void CargarPerfiles()
    {
        _view.MostrarCargando(true);

        var perfiles = await _perfilService.ObtenerPerfilesAsync();

        _view.MostrarCargando(false);
        _view.MostrarPerfiles(perfiles);
    }

    private void HandleSeleccionarPerfil(string nombre)
    {
        // Si el perfil tiene datos, lo carga y va al juego
        // Si no, muestra el panel de creación para ese slot
        var perfil = _perfilService.ObtenerPerfil(nombre);

        if (perfil.TieneDatos)
        {
            _perfilService.EstablecerPerfilActivo(perfil);
            Navigator.NavigateTo(ScreenManager.Screen.Ingame);
        }
        else
        {
            _view.MostrarPanelCreacion();
        }
    }

    private async void HandleConfirmarCreacion(string nombre)
    {
        if (string.IsNullOrWhiteSpace(nombre))
        {
            _view.MostrarError("El nombre no puede estar vacío.");
            return;
        }

        _view.MostrarCargando(true);

        var exito = await _perfilService.CrearPerfilAsync(nombre);

        _view.MostrarCargando(false);

        if (exito)
            Navigator.NavigateTo(ScreenManager.Screen.Ingame);
        else
            _view.MostrarError("No se pudo crear el perfil. Inténtalo de nuevo.");
    }

    private void HandleVolver()
    {
        Navigator.NavigateTo(ScreenManager.Screen.MenuPrincipal);
    }
}