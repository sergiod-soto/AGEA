using System;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// View de la pantalla de preferencias.
/// Por ahora: configuracion de conexion al servidor Python (IP + puerto).
/// </summary>
public class PreferencesView : MonoBehaviour
{
    // ── Eventos que el Presenter escucha ─────────────────────────────────────
    public event Action OnVolver;
    public event Action<string, int> OnGuardar;   // ip, puerto

    // ── Referencias UI (asignar en Inspector) ────────────────────────────────
    [Header("Conexión")]
    [SerializeField] private TMP_InputField inputIP;
    [SerializeField] private TMP_InputField inputPuerto;

    [Header("Acciones")]
    [SerializeField] private Button btnGuardar;
    [SerializeField] private Button btnVolver;

    [Header("Feedback")]
    [SerializeField] private TMP_Text textoError;
    [SerializeField] private TMP_Text textoConfirmacion;

    // ── Unity ────────────────────────────────────────────────────────────────

    private void Awake()
    {
        btnVolver.onClick.AddListener(() => OnVolver?.Invoke());
        btnGuardar.onClick.AddListener(HandleGuardar);

        // Puerto solo acepta numeros
        inputPuerto.contentType = TMP_InputField.ContentType.IntegerNumber;
    }

    // ── API que el Presenter usa ─────────────────────────────────────────────

    public void CargarValores(string ip, int puerto)
    {
        inputIP.text = ip;
        inputPuerto.text = puerto.ToString();
    }

    public void MostrarError(string mensaje)
    {
        textoError.text = mensaje;
        textoError.enabled = !string.IsNullOrEmpty(mensaje);
        textoConfirmacion.enabled = false;
    }

    public void MostrarConfirmacion(string mensaje)
    {
        textoConfirmacion.text = mensaje;
        textoConfirmacion.enabled = !string.IsNullOrEmpty(mensaje);
        textoError.enabled = false;
    }

    // ── Privados ─────────────────────────────────────────────────────────────

    private void HandleGuardar()
    {
        // La validacion de formato la hace la View (es responsabilidad de UI)
        // La validacion de negocio (si la IP es alcanzable) la hace el Presenter
        if (!int.TryParse(inputPuerto.text, out int puerto))
        {
            MostrarError("El puerto debe ser un número.");
            return;
        }

        OnGuardar?.Invoke(inputIP.text.Trim(), puerto);
    }
}