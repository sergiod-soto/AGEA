using UnityEngine;

[RequireComponent(typeof(ControlHUD))]
public class Perfil : MonoBehaviour
{
    GameObject HUDBase;
    void Start()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }

    public void AbrirPerfiles()
    {
        HUDBase.transform.Find("HUD Running").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Pantalla Inicio").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(true);
    }

    public void CerrarPerfiles()
    {
        HUDBase.transform.Find("HUD Running").gameObject.SetActive(false);
        HUDBase.transform.Find("HUD Pantalla Inicio").gameObject.SetActive(true);
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);
    }

    public void Atras()
    {
        CerrarPerfiles();
    }

}
