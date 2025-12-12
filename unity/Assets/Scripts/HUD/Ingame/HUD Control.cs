using UnityEngine;

public class HUDControl : MonoBehaviour, IHUDRunningControl
{

    IControlHUDLogica controlHUD;
    void Awake()
    {
        controlHUD = ServiceLocator.Instance.Get<IControlHUDLogica>();
    }

    public void Show_HUD()
    {
        Debug.Log("asdasd");
        controlHUD.OpenBotHUD();
    }

    public void Hide_HUD()
    {
       controlHUD.CloseBotHUD();
    }
   
}
