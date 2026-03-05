using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil5 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(5);
    }
}
