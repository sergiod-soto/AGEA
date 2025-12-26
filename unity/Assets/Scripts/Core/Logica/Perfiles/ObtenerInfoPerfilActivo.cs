using UnityEngine;

public class SolicitarInfoPerfilActivo : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void SolicitarInfo()
    {
        conexion.EnviarMensaje("{\"tipo\":\"perfil\",\"peticion\":\"info_perfil_activo\"}");
    }
}
