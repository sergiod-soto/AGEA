using UnityEngine;

public class ControlHUD : MonoBehaviour, IControlHUDLogica
{
    public GameObject HUDBase;

    void Start()
    {
        SetBaseState();
    }

    /*
     * se hace clic en cerrar HUD (en el boton). 
     */
    public void CloseBotHUD()
    {
        throw new System.NotImplementedException();

    }

    /*
     * entramos en preferences
     */
    public void EnterOptions()
    {
        throw new System.NotImplementedException();
    }

    /*
     * se hace clic en "suelo"
     */
    public void ExitBotHUD()
    {
        HUDBase.transform.Find("HUD Running").Find("HUD Info Bot").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Running").Find("Show HUD False").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Running").Find("Show HUD True").gameObject.SetActive(false);
    }

    /*
     * al cerrar las opciones
     */
    public void ExitOptions()
    {
        throw new System.NotImplementedException();
    }

    /*
     * se sale al menu principal
     */
    public void LeaveGame()
    {
        SetBaseState();
    }

    /*
     * al hacer clic en un bot
     */
    public void OpenBotHUD()
    {
        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        GameObject HUDInfoBot = HUDRunning.transform.Find("HUD Info Bot").gameObject;
        HUDInfoBot.SetActive(true);

        GameObject PanelBase = HUDInfoBot.transform.Find("Panel Base").gameObject;
        PanelBase.SetActive(true);

        // base
        PanelBase.transform.Find("Posicion Text").gameObject.SetActive(true);
        PanelBase.transform.Find("Posicion Value").gameObject.SetActive(true);
        PanelBase.transform.Find("Panel").gameObject.SetActive(true);
        PanelBase.transform.Find("ID Text").gameObject.SetActive(true);
        PanelBase.transform.Find("ID Value").gameObject.SetActive(true);

        GameObject Propiedades = PanelBase.transform.Find("Propiedades").gameObject;
        Propiedades.SetActive(true);

        GameObject BasePropBase = Propiedades.transform.Find("Base Prop Base").gameObject;
        BasePropBase.SetActive(true);

        BasePropBase.transform.Find("Propiedades Text").gameObject.SetActive(true);
        BasePropBase.transform.Find("Propiedades Value").gameObject.SetActive(true);
        BasePropBase.transform.Find("Mostrar Propiedades Avanzadas").gameObject.SetActive(true);

        GameObject BasePropAvanzadas = Propiedades.transform.Find("Base Prop Avanzadas").gameObject;
        BasePropAvanzadas.SetActive(false);

        PanelBase.transform.Find("Boton Familia").gameObject.SetActive(true);
        PanelBase.transform.Find("Base Familia").gameObject.SetActive(false);
        PanelBase.transform.Find("Boton Modificadores").gameObject.SetActive(true);
        PanelBase.transform.Find("Base Modificadores").gameObject.SetActive(false);

        HUDRunning.transform.Find("Show HUD True").gameObject.SetActive(false);
        HUDRunning.transform.Find("Show HUD False").gameObject.SetActive(true);
    }

    /*
     *  justo tras hacer clic en Start
     */
    public void SetBaseState()
    {
        // BASE HUD  //////////////////////////////////////////////////////////////////////////////////
        HUDBase.SetActive(true);

        // HUD Running  //////////////////////////////////////////////////////////////////////////////
        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        HUDRunning.SetActive(false);

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

    /*
     *  justo tras arrancar el programa
     */
    public void StartGame()
    {
        // HUD Pantalla Inicio  ///////////////////////////////////////////////////////////////////////////////
        HUDBase.transform.Find("HUD Pantalla Inicio").gameObject.SetActive(false);


        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        HUDRunning.SetActive(true);

        HUDRunning.transform.Find("Boton Pause").gameObject.SetActive(true);

        GameObject HUDInfoBot = HUDRunning.transform.Find("HUD Info Bot").gameObject;
        HUDInfoBot.SetActive(false);

        GameObject FondoOpciones = HUDRunning.transform.Find("Fondo Opciones").gameObject;
        FondoOpciones.SetActive(true);

        FondoOpciones.transform.Find("Opciones").gameObject.SetActive(true);
    }
}
