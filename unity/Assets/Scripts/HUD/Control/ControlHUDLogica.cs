using UnityEngine;

[RequireComponent(typeof(GameControl))]
[RequireComponent(typeof(Bot))]
[RequireComponent(typeof(Options))]
[RequireComponent(typeof(Perfil))]
[RequireComponent(typeof(ControlMenu))]

public class ControlHUD : MonoBehaviour, IControlHUDLogica
{
    public GameObject HUDBase;

    void Start()
    {
        SetBaseState();
    }

    /*
     * se oculta el HUD (por el boton). 
     */
    public void ShowBotHUDFalse()
    {
        GetComponent<Bot>().CloseBotHUD();
    }

    /*
     * se muestra el HUD (por el boton). 
     */
    public void ShowBotHUDTrue()
    {
        GetComponent<Bot>().OpenBotHUD();
    }

    /*
     * entramos en preferences
     */
    public void EnterOptions()
    {
        GetComponent<Options>().EnterOptions();
    }

    /*
    * al cerrar las opciones
    */
    public void ExitOptions()
    {
        GetComponent<Options>().ExitOptions();
    }

    /*
     * se hace clic en "suelo"
     */
    public void CloseBotHUD()
    {
        GetComponent<Bot>().CloseBotHUD();
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
        GetComponent<Bot>().OpenBotHUD();
    }

    /*
     *  justo tras hacer clic en Start
     */
    public void SetBaseState()
    {
        GetComponent<GameControl>().SetBaseState();
    }

    /*
     *  justo tras arrancar el programa
     */
    public void StartGame()
    {
        GetComponent<GameControl>().StartGame();
    }


    public void AbrirPerfiles()
    {
        GetComponent<Perfil>().AbrirPerfiles();
    }

    public void CerrarPerfiles()
    {
        GetComponent<Perfil>().CerrarPerfiles();
    }

    public void AbrirNuevoPerfil()
    {
        GetComponent<ControlMenu>().AbrirNuevoPerfil();
    }
}
