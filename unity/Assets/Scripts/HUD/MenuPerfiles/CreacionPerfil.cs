using UnityEngine;

public class ControlMenu : MonoBehaviour
{
    GameObject HUDBase;



    /*
     * Se abre el menu de crear nuevo perfil
     */
    public void AbrirNuevoPerfil()
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Nuevo Perfil").gameObject.SetActive(true);
    }

    public void AtrasNuevoPerfil()
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(true);
        HUDBase.transform.Find("HUD Nuevo Perfil").gameObject.SetActive(false);
    }
}
