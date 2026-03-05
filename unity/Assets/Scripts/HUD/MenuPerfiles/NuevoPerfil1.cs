using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil1 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(1);
    }
}