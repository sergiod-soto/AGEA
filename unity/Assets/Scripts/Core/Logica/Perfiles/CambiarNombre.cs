using UnityEngine;
using UnityEngine.UIElements;

public class CambiarNombre : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void ChangeName(string nuevoNombre)
    {
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"cambio_nombre\",\"nombre\":\"" + nuevoNombre + "\"}");
    }
}
