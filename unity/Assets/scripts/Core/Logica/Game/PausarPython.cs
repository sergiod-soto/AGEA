using Newtonsoft.Json.Linq;
using UnityEngine;

public class Pausar : MonoBehaviour
{
    IConexionMundo conexion;
    private void Start()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }


    public void PausePython()
    {
        Debug.Log("mandando pausa");
        conexion.EnviarMensaje("{\"tipo\":\"pausa\"}");
    }
}
