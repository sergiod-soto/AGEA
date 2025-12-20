using UnityEngine;

public class CambiarPerfil : MonoBehaviour
{
    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    public void ChangeActiveProfile(string profileName)
    {
        conexion.EnviarMensaje("{\"tipo\":\"perfil\",\"peticion\":\"cambiar_perfil\",\"nombre\":\"" + profileName + "\"}");
    }
}
