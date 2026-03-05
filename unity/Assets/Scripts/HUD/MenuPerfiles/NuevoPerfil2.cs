using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil2 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(2);
    }
}
