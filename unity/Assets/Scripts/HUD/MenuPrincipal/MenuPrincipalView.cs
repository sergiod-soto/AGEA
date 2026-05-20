using System;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// View del menu principal.
/// Tres botones: Start, Preferences, Exit.
/// Nada más.
/// </summary>
public class MenuPrincipalView : MonoBehaviour
{
    // ── Eventos que el Presenter escucha ─────────────────────────────────────
    public event Action OnStart;
    public event Action OnPreferences;
    public event Action OnExit;

    // ── Referencias UI (asignar en Inspector) ────────────────────────────────
    [SerializeField] private Button btnStart;
    [SerializeField] private Button btnPreferences;
    [SerializeField] private Button btnExit;

    // ── Unity ────────────────────────────────────────────────────────────────

    private void Awake()
    {
        btnStart.onClick.AddListener(()       => OnStart?.Invoke());
        btnPreferences.onClick.AddListener(() => OnPreferences?.Invoke());
        btnExit.onClick.AddListener(()        => OnExit?.Invoke());
    }
}