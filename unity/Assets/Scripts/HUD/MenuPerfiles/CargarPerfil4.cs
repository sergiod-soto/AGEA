using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil4 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(4);
    }
}
