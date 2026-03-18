using UnityEngine;

[RequireComponent(typeof(IPerfilesLogica))]
[RequireComponent(typeof(ControlHUD))]

public class CargaPerfil : MonoBehaviour
{

    GameObject HUDBase;


    void Awake()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }

    public void CargarPerfil(int id)
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);
    }
}
