using Newtonsoft.Json.Linq;
using UnityEngine;

public class ObtenerInfoPerfilActivo : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void ObtenerInfo()
    {
        conexion.EnviarMensaje("{\"tipo\":\"perfil\",\"peticion\":\"info_perfil_activo\"}");
    }
}
