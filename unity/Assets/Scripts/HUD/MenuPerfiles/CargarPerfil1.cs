using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil1 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(1);
    }
}
