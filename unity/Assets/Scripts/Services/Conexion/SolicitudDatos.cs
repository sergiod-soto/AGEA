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
        if (objeto.TryGetComponent<BotInfo>(out _))
        {
            SolicitarDatosBot(objeto);
        }

    }

    void SolicitarDatosBot(GameObject bot)
    {
        conexion.EnviarMensaje("{\"tipo\":\"dato\",\"entity\":\"bot\",\"id\":\"" + bot.GetComponent<BotInfo>().id + "\"}");
    }
}
