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
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"info_perfil_activo\"}");
    }
}
