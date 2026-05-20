using Newtonsoft.Json.Linq;
using UnityEngine;

/// <summary>
/// Procesa todos los mensajes entrantes de Python en cada frame.
/// Enruta cada mensaje al servicio correspondiente según el campo "peticion".
/// </summary>
public class DigestionAccionesPendientes : MonoBehaviour, IProcesamientoEntradaConexion
{
    IConexionMundo conexionMundo;
    IBotsLogica logicaBots;
    IPerfilService perfilService;

    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
        logicaBots = ServiceLocator.Instance.Get<IBotsLogica>();
        perfilService = ServiceLocator.Instance.Get<IPerfilService>();
    }

    void Update()
    {
        // Vaciamos toda la cola de una vez
        while (conexionMundo.GetAccionesPendientes().TryDequeue(out JObject json))
        {
            DigerirEntrada(json);
        }
    }

    public void DigerirEntrada(JObject json)
    {
        if (json == null) return;

        var peticion = json["peticion"]?.ToString();
        if (peticion == null)
        {
            Debug.LogWarning("[Digestion] Mensaje recibido sin campo 'peticion':\n" + json);
            return;
        }

        switch (peticion)
        {
            case "actualizacion":
                logicaBots.ActualizarBots((JArray)json["bots"]);
                break;

            case "dato":
                logicaBots.ActualizarHUDDatosBot((JObject)json["bot"]);
                break;

            case "perfil":
                perfilService.ProcesarRespuesta(json);
                break;

            default:
                Debug.LogWarning($"[Digestion] Tipo de petición desconocido: '{peticion}'");
                break;
        }
    }
}