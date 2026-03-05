using UnityEngine;

[RequireComponent(typeof(CargaPerfil))]
public class CargarPerfil6 : MonoBehaviour
{
    public void Cargar()
    {
        GetComponent<CargaPerfil>().CargarPerfil(6);
    }
}
