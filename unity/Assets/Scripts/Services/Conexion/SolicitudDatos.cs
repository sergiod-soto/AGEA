using Newtonsoft.Json.Linq;
using UnityEngine;

public class SolicitudDatos : MonoBehaviour, ISolicitudDatos
{
    IConexionMundo conexion;

    void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    public void SolicitarDatos(GameObject objeto)
    {
        if (objeto.TryGetComponent<BotInfo>(out BotInfo botInfo))
            SolicitarDatosBot(botInfo);
    }

    void SolicitarDatosBot(BotInfo bot)
    {
        var msg = new JObject
        {
            ["peticion"] = "dato",
            ["entity"] = "bot",
            ["id"] = bot.id
        };
        conexion.EnviarMensaje(msg.ToString(Newtonsoft.Json.Formatting.None));
    }
}