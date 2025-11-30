using UnityEngine;

public class Pruebas : MonoBehaviour
{

    IConexionMundo conexionMundo;

    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    public void Test()
    {
        conexionMundo.EnviarMensaje("{\"tipo\":\"dato\",\"id\":\"" + 1 + "\"}");
    }
}
