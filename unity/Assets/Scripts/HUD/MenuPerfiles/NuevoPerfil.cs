using UnityEngine;

[RequireComponent(typeof(ControlHUD))]
public class NuevoPerfil : MonoBehaviour
{
    GameObject HUDBase;


    void Awake()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }

    /*
     * Se abre el menu de crear nuevo perfil
     */
    public void AbrirNuevoPerfil(int id)
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Nuevo Perfil").gameObject.SetActive(true);
    }

    public void AtrasNuevoPerfil()
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(true);
        HUDBase.transform.Find("HUD Nuevo Perfil").gameObject.SetActive(false);
    }

    /*
     * se manda solicitud a python para crear nuevo perfil
     */
    public void CrearPerfil(int id)
    {

    }
}
