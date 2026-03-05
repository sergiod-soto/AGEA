using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil3 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(3);
    }
}
