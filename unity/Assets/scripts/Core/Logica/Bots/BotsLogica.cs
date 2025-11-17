using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;

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

    public void ClicEnBot(bot_info bot_inf)
    {
        GetComponent<ObtenerDatos>().ClicEnBot(bot_inf);
    }

    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject)
    {
        GetComponent<RenderizarBots>().Renderizar(bots_gameObject);
    }

}
