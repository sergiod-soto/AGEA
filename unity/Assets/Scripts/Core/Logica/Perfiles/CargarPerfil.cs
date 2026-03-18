using UnityEngine;

public class CargarPerfil : MonoBehaviour
{
    IConexionMundo conexion;

    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void Cargar(int id)
    {
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"cargar_perfil\",\"id\":\"" + id + "}");
    }
}
