using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(GeneradorBot))]
[RequireComponent(typeof(SolicitarDatos))]
[RequireComponent(typeof(RenderizarBots))]
[RequireComponent(typeof(ActualizarBots))]
[RequireComponent(typeof(EliminarBot))]
public class BotsLogica : MonoBehaviour, IBotsLogica
{


    public GameObject CreateBot(JObject datos)
    {
        return GetComponent<GeneradorBot>().CreateBot(datos);
    }

    public void ClicEnBot(GameObject bot)
    {
        GetComponent<SolicitarDatos>().ClicEnBot(bot);
    }

    public void ActualizarHUDDatosBot(JObject bot)
    {
        GetComponent<SolicitarDatos>().ActualizarHUD(bot);
    }

    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject)
    {
        GetComponent<RenderizarBots>().Renderizar();
    }

    public void ActualizarBots(JArray bots)
    {
        GetComponent<ActualizarBots>().ActualizarBotsMetodo(bots);
    }

    public void EliminarBot(Dictionary<string, GameObject> diccionarioBots, string idBot)
    {
        GetComponent<EliminarBot>().EliminarBotMetodo(diccionarioBots, idBot);
    }

}
