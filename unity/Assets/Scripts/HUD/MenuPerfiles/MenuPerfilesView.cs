using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// View de la pantalla de perfiles.
/// Responsabilidad ÚNICA: reflejar lo que el Presenter le diga y notificarle las acciones del usuario.
/// No toma ninguna decisión. No llama a ningún servicio.
/// </summary>
public class MenuPerfilesView : MonoBehaviour
{
    // ?? Eventos que el Presenter escucha ?????????????????????????????????????
    public event Action OnVolver;
    public event Action<string> OnSeleccionarPerfil;   // nombre del perfil seleccionado
    public event Action<string> OnConfirmarCreacion;   // nombre introducido por el usuario

    // ?? Referencias UI (asignar en Inspector) ????????????????????????????????
    [Header("Panel: Lista de perfiles")]
    [SerializeField] private GameObject panelLista;
    [SerializeField] private Transform contenedorPerfiles;   // padre de los items
    [SerializeField] private GameObject prefabItemPerfil;     // prefab con botón + nombre
    [SerializeField] private Button btnVolver;

    [Header("Panel: Crear perfil")]
    [SerializeField] private GameObject panelCreacion;
    [SerializeField] private TMP_InputField inputNombre;
    [SerializeField] private Button btnConfirmar;
    [SerializeField] private Button btnCancelar;

    [Header("Estado")]
    [SerializeField] private GameObject panelCargando;
    [SerializeField] private TMP_Text textoError;

    // ?? Unity ????????????????????????????????????????????????????????????????

    private void Awake()
    {
        btnVolver.onClick.AddListener(() => OnVolver?.Invoke());
        btnConfirmar.onClick.AddListener(() => OnConfirmarCreacion?.Invoke(inputNombre.text));
        btnCancelar.onClick.AddListener(() => MostrarPanelLista());
    }

    // ?? API que el Presenter usa ?????????????????????????????????????????????

    public void MostrarPerfiles(List<DatosPerfil> perfiles)
    {
        // Limpiar items anteriores
        foreach (Transform hijo in contenedorPerfiles)
            Destroy(hijo.gameObject);

        foreach (var perfil in perfiles)
        {
            var item = Instantiate(prefabItemPerfil, contenedorPerfiles);
            var texto = item.GetComponentInChildren<TMP_Text>();
            var boton = item.GetComponentInChildren<Button>();

            texto.text = perfil.Nombre;

            // Captura de variable local para el closure
            var nombreCapturado = perfil.Nombre;
            boton.onClick.AddListener(() => OnSeleccionarPerfil?.Invoke(nombreCapturado));

            // Si el perfil no tiene datos, se muestra visualmente diferente
            boton.interactable = perfil.TieneDatos;
        }

        MostrarPanelLista();
    }

    public void MostrarPanelCreacion()
    {
        panelLista.SetActive(false);
        panelCreacion.SetActive(true);
        inputNombre.text = string.Empty;
        inputNombre.Select();
    }

    public void MostrarCargando(bool activo)
    {
        panelCargando.SetActive(activo);
    }

    public void MostrarError(string mensaje)
    {
        textoError.text = mensaje;
        textoError.enabled = !string.IsNullOrEmpty(mensaje);
    }

    // ?? Privados ?????????????????????????????????????????????????????????????

    private void MostrarPanelLista()
    {
        panelLista.SetActive(true);
        panelCreacion.SetActive(false);
        MostrarError(string.Empty);
    }
}
