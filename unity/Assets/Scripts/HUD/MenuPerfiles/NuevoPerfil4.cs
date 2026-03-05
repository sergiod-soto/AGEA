using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil4 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(4);
    }
}
