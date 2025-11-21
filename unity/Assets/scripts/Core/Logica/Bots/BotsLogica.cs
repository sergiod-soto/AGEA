using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(GeneradorBot))]
[RequireComponent(typeof(ObtenerDatos))]
[RequireComponent(typeof(RenderizarBots))]
[RequireComponent(typeof(BotClicked))]
[RequireComponent(typeof(ActualizarBots))]
[RequireComponent(typeof(EliminarBot))]
public class BotsLogica : MonoBehaviour, IBotsLogica
{
    public void OnClic()
    {
        GetComponent<BotClicked>().OnClick();
    }

    public GameObject CreateBot(JObject datos)
    {
        return GetComponent<GeneradorBot>().CreateBot(datos);
    }

    public void ClicEnBot(BotInfo bot_inf)
    {
        GetComponent<ObtenerDatos>().ClicEnBot(bot_inf);
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
