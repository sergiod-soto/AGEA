using UnityEngine;

public class NuevoPerfil : MonoBehaviour
{
    IControlHUDLogica controlHUDLogica;
    void Awake()
    {
        controlHUDLogica = ServiceLocator.Instance.Get<IControlHUDLogica>();
    }

    public void CrearPerfil(int id)
    {

    }
}
