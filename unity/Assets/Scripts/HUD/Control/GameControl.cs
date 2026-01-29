using UnityEngine;

[RequireComponent(typeof(ControlHUD))]
public class GameControl : MonoBehaviour
{
    GameObject HUDBase;

    void Awake()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }
    public void StartGame()
    {
        // HUD Pantalla Inicio  ///////////////////////////////////////////////////////////////////////////////
        HUDBase.transform.Find("HUD Pantalla Inicio").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);


        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        HUDRunning.SetActive(true);

        HUDRunning.transform.Find("Boton Pause").gameObject.SetActive(true);

        GameObject HUDInfoBot = HUDRunning.transform.Find("HUD Info Bot").gameObject;
        HUDInfoBot.SetActive(false);

        GameObject FondoOpciones = HUDRunning.transform.Find("Fondo Opciones").gameObject;
        FondoOpciones.SetActive(true);

        FondoOpciones.transform.Find("Opciones").gameObject.SetActive(true);
    }

    public void SetBaseState()
    {    
        // BASE HUD  //////////////////////////////////////////////////////////////////////////////////
        HUDBase.SetActive(true);

        // HUD Running  //////////////////////////////////////////////////////////////////////////////
        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        HUDRunning.SetActive(false);

        // HUD Perfiles  ///////////////////////////////////////////////////////////////////////////////
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);

        // HUD Pantalla Inicio  ///////////////////////////////////////////////////////////////////////////////
        GameObject HUDPantallaInicio = HUDBase.transform.Find("HUD Pantalla Inicio").gameObject;
        HUDPantallaInicio.SetActive(true);

        HUDPantallaInicio.transform.Find("Fondo").gameObject.SetActive(true);

        GameObject Botones = HUDPantallaInicio.transform.Find("Botones").gameObject;
        Botones.SetActive(true);

        Botones.transform.Find("Start").gameObject.SetActive(true);
        Botones.transform.Find("Preferences").gameObject.SetActive(true);
        Botones.transform.Find("Exit").gameObject.SetActive(true);
    }
}
