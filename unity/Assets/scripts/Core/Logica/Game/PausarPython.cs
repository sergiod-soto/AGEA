using Newtonsoft.Json.Linq;
using UnityEngine;

public class Pausar : MonoBehaviour
{
    IConexionMundo conexion;
    private void Start()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }


    public void Pause()
    {
        Debug.Log("Enviando pausa al mundo Python");
        var msg = new JObject { 
            ["tipo"] = "pause"
        };

        conexion.EnviarMensaje(msg.ToString(Newtonsoft.Json.Formatting.None));
    }
}
