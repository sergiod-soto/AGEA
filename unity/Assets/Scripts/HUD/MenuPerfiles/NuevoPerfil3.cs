using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil3 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(3);
    }
}
