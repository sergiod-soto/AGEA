using UnityEngine;

public class HUDControl : MonoBehaviour, IHUDRunningControl
{

    public GameObject HUDRunning;
    public GameObject hideHUDBoton;

    public void Show_HUD()
    {
        HUDRunning.SetActive(true);
        hideHUDBoton.SetActive(true);
    }

    public void Hide_HUD()
    {
        HUDRunning.SetActive(false);
        hideHUDBoton.SetActive(false);
    }
   
}
