using UnityEngine;

public class CrearPerfil : MonoBehaviour
{
    IConexionMundo conexion;

    void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    public void CrearNuevoPerfil(string idPerfil, string nombre)
    {
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"crear_perfil\",\"id\":\"" + idPerfil + "\",\"nombre\":" + nombre + "}");
    }
}
