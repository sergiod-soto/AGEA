using Newtonsoft.Json.Linq;
using UnityEngine;

public class SolicitarPerfiles : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void SolicitarListaPerfiles()
    {
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"obtener_perfiles\"}");
    }
     
}
