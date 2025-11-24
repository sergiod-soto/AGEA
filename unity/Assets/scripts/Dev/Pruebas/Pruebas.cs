using UnityEngine;

public class Pruebas : MonoBehaviour
{

    IConexionMundo conexionMundo;

    void Start()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    public void Test()
    {
        conexionMundo.EnviarMensaje("{\"tipo\":\"actualizacion\"}");
    }
}
