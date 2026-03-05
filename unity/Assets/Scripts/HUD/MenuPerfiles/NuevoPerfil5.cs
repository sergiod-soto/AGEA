using UnityEngine;

[RequireComponent(typeof(NuevoPerfil))]
public class NuevoPerfil5 : MonoBehaviour
{
    public void CrearPerfil()
    {
        GetComponent<NuevoPerfil>().CrearPerfil(5);
    }
}
