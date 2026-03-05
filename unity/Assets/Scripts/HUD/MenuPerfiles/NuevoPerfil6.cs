using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil6 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(6);
    }
}
