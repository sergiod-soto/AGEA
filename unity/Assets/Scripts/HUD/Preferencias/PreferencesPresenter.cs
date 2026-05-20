using UnityEngine;

/// <summary>
/// Presenter de la pantalla de preferencias.
/// Gestiona la configuración de conexión al servidor Python.
/// Los valores se persisten en PlayerPrefs al ser configuración del cliente,
/// no del perfil de juego.
/// </summary>
public class PreferencesPresenter : PresenterBase
{
    private readonly PreferencesView _view;
    private readonly IConexionMundo _conexion;

    // Claves de PlayerPrefs
    private const string KEY_IP = "conexion_ip";
    private const string KEY_PUERTO = "conexion_puerto";

    // Valores por defecto
    private const string IP_DEFAULT = "127.0.0.1";
    private const int PUERTO_DEFAULT = 5000;

    public PreferencesPresenter(PreferencesView view, ScreenManager navigator)
        : base(navigator)
    {
        _view = view;
        _conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    // ── Ciclo de vida ─────────────────────────────────────────────────────────

    public override void Initialize()
    {
        _view.OnVolver += HandleVolver;
        _view.OnGuardar += HandleGuardar;

        // Carga los valores guardados o los defaults
        var ip = PlayerPrefs.GetString(KEY_IP, IP_DEFAULT);
        var puerto = PlayerPrefs.GetInt(KEY_PUERTO, PUERTO_DEFAULT);
        _view.CargarValores(ip, puerto);
    }

    public override void Dispose()
    {
        _view.OnVolver -= HandleVolver;
        _view.OnGuardar -= HandleGuardar;
    }

    // ── Handlers ─────────────────────────────────────────────────────────────

    private void HandleGuardar(string ip, int puerto)
    {
        if (!ValidarIP(ip))
        {
            _view.MostrarError("La dirección IP no es válida.");
            return;
        }

        if (!ValidarPuerto(puerto))
        {
            _view.MostrarError("El puerto debe estar entre 1024 y 65535.");
            return;
        }

        PlayerPrefs.SetString(KEY_IP, ip);
        PlayerPrefs.SetInt(KEY_PUERTO, puerto);
        PlayerPrefs.Save();

        _view.MostrarConfirmacion("Configuración guardada. Se aplicará en la próxima conexión.");
    }

    private void HandleVolver()
    {
        Navigator.NavigateTo(ScreenManager.Screen.MenuPrincipal);
    }

    // ── Validación ────────────────────────────────────────────────────────────

    private bool ValidarIP(string ip)
    {
        if (string.IsNullOrWhiteSpace(ip)) return false;

        // Acepta tanto IPv4 como hostname (ej: "mi-servidor.local")
        return System.Net.IPAddress.TryParse(ip, out _) || ip.Length > 0;
    }

    private bool ValidarPuerto(int puerto) => puerto is >= 1024 and <= 65535;
}