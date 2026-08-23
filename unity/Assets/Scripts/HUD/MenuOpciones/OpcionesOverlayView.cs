// Assets/Scripts/HUD/MenuOpciones/OpcionesOverlayView.cs
using System;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Panel de "Opciones" DURANTE la partida.
///
/// Decisión acordada: esto NO es una Screen gestionada por ScreenManager.
/// Es un overlay local sobre IngameView -- la simulación sigue en vivo
/// detrás mientras está abierto, y cerrarlo no reconstruye nada.
///
/// IngameView es quien posee la referencia (SerializeField) y reenvía
/// OnVolverAlMenu como su propio evento; así IngamePresenter sigue
/// hablando solo con IngameView (MVP intacto) y no conoce la existencia
/// de este sub-componente. "Volver al menú" sí implica una navegación
/// real, así que ese evento burbujea hasta el Presenter, que es quien
/// tiene acceso al Navigator.
/// </summary>
public class OpcionesOverlayView : MonoBehaviour
{
    public event Action OnVolverAlMenu;

    [SerializeField] private GameObject panel;
    [SerializeField] private Button btnVolverAlMenu;
    [SerializeField] private Button btnCerrar;

    private void Awake()
    {
        btnVolverAlMenu.onClick.AddListener(() => OnVolverAlMenu?.Invoke());
        btnCerrar.onClick.AddListener(Cerrar);
        panel.SetActive(false);
    }

    /// <summary>Abre el panel si está cerrado, lo cierra si está abierto.</summary>
    public void Alternar() => panel.SetActive(!panel.activeSelf);

    public void Cerrar() => panel.SetActive(false);
}