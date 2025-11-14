using Newtonsoft.Json.Linq;
using UnityEngine;

public class Pausar : MonoBehaviour
{
    public void Pause()
    {
        Debug.Log("Enviando pausa al mundo Python");
        var msg = new JObject { 
            ["tipo"] = "pause"
        };

        GetComponent<ConexionMundo>().EnviarMensaje(msg.ToString(Newtonsoft.Json.Formatting.None));
    }
}
