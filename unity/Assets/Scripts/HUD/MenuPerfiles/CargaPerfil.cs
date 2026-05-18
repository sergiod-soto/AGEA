using UnityEngine;

[RequireComponent(typeof(IPerfilesLogica))]

public class CargaPerfil : MonoBehaviour
{

    GameObject HUDBase;


    public void CargarPerfil(int id)
    {
        HUDBase.transform.Find("HUD Perfiles").gameObject.SetActive(false);
    }
}
