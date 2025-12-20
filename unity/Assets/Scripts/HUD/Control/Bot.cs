using UnityEngine;

[RequireComponent(typeof(ControlHUD))]
public class Bot : MonoBehaviour
{
    GameObject HUDBase;

    void Start()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }

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

        HUDRunning.transform.Find("Show HUD").gameObject.SetActive(true);
    }

    /*
     * se hace clic en "suelo"
     */
    public void CloseBotHUD()
    {
        HUDBase.transform.Find("HUD Running").Find("HUD Info Bot").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Running").Find("Show HUD").gameObject.SetActive(false);
    }

    /*
     * se oculta el HUD (por el boton). 
     */
    public void ShowBotHUDFalse()
    {
        HUDBase.transform.Find("HUD Running")
            .transform.Find("HUD Info Bot").gameObject.SetActive(false);
    }

    /*
     * se muestra el HUD (por el boton). 
     */
    public void ShowBotHUDTrue()
    {
        HUDBase.transform.Find("HUD Running")
            .transform.Find("HUD Info Bot").gameObject.SetActive(true);
    }
}
