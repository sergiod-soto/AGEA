// Assets/Scripts/HUD/MenuPrincipal/MenuPrincipalPresenter.cs
using UnityEngine;

/// <summary>
/// Presenter del menu principal.
/// Decide a donde va cada boton.
/// </summary>
public class MenuPrincipalPresenter : PresenterBase
{
    private readonly MenuPrincipalView _view;

    public MenuPrincipalPresenter(MenuPrincipalView view, ScreenManager navigator)
        : base(navigator)
    {
        _view = view;
    }

    // ── Ciclo de vida ────────────────────────────────────────────────────────

    public override void Initialize()
    {
        _view.OnStart += HandleStart;
        _view.OnPreferences += HandlePreferences;
        _view.OnExit += HandleExit;
    }

    public override void Dispose()
    {
        _view.OnStart -= HandleStart;
        _view.OnPreferences -= HandlePreferences;
        _view.OnExit -= HandleExit;
    }

    // ── Handlers ─────────────────────────────────────────────────────────────

    private void HandleStart()
    {
        // Perfiles eliminado del alcance actual: Start entra directo a la partida.
        Navigator.NavigateTo(ScreenManager.Screen.Ingame);
    }

    private void HandlePreferences()
    {
        Navigator.NavigateTo(ScreenManager.Screen.Preferences);
    }

    private void HandleExit()
    {
        Application.Quit();

        // En el editor no hace nada, esto lo activa:
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#endif
    }
}