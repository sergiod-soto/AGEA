using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil2 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(2);
    }
}
