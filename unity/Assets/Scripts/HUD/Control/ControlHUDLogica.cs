using UnityEngine;

public class ControlHUD : MonoBehaviour, IControlHUDLogica
{
    public GameObject HUDBase;

    void Start()
    {
        SetBaseState();
    }

    public void CloseBotHUD()
    {
        throw new System.NotImplementedException();
    }

    public void EnterOptions()
    {
        throw new System.NotImplementedException();
    }

    public void ExitBotHUD()
    {
        throw new System.NotImplementedException();
    }

    public void ExitOptions()
    {
        throw new System.NotImplementedException();
    }

    public void LeaveGame()
    {
        throw new System.NotImplementedException();
    }

    public void OpenBotHUD()
    {
        GameObject HUDRunning = HUDBase.transform.Find("HUD Running").gameObject;
        GameObject HUDInfoBot = HUDRunning.transform.Find("HUD Info Bot").gameObject;
        HUDInfoBot.SetActive(true);

        GameObject PanelBase = HUDInfoBot.transform.Find("Panel Base").gameObject;
        PanelBase.SetActive(true);

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




        GameObject BaseFamilia = PanelBase.transform.Find("Base Familia").gameObject;
        BaseFamilia.SetActive(true);

        BaseFamilia.transform.Find("Apellidos Text").gameObject.SetActive(true);
        BaseFamilia.transform.Find("Apellidos Value").gameObject.SetActive(true);
        BaseFamilia.transform.Find("Boton Atras").gameObject.SetActive(true);

        PanelBase.transform.Find("Boton Modificadores").gameObject.SetActive(true);

        GameObject BaseModificadores = PanelBase.transform.Find("Base Modificadores").gameObject;
        BaseFamilia.SetActive(true);

        BaseModificadores.transform.Find("Modificadores Value").gameObject.SetActive(true);
        BaseModificadores.transform.Find("Boton Atras Modificadores").gameObject.SetActive(true);

        HUDRunning.transform.Find("Show HUD True").gameObject.SetActive(true);
        HUDRunning.transform.Find("Show HUD False").gameObject.SetActive(false);
    }

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
