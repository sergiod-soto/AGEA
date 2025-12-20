using Newtonsoft.Json.Linq;
using UnityEngine;

public class ObtenerPerfiles : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void ObtenerListaPerfiles()
    {
        conexion.EnviarMensaje("{\"tipo\":\"perfil\",\"peticion\":\"obtener_perfiles\"}");
    }
}
