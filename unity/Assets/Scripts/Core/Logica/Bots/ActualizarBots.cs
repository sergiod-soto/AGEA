using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class ActualizarBots : MonoBehaviour
{
    IBotsGameobjectData datosBots;
    IBotsLogica logicaBots;
    void Start()
    {
        datosBots = ServiceLocator.Instance.Get<IBotsGameobjectData>();
        logicaBots = ServiceLocator.Instance.Get<IBotsLogica>();
    }


    public void ActualizarBotsMetodo(JArray bots)
    {
        Dictionary<string, GameObject> diccionarioBots = datosBots.Bots_GameObjects;
        Dictionary<string, GameObject> botsAux = new(diccionarioBots); // copia para detectar bots eliminados
        foreach (JObject bot in bots)
        {
            if (!diccionarioBots.ContainsKey(bot["id"].ToString()))
            {
                // No existe, por lo que se crea
                logicaBots.CreateBot(bot);
            }
            else
            {
                // Existe, por lo que se actualiza
                datosBots.Bots_GameObjects[bot["id"].ToString()].GetComponent<BotInfo>().ActualizarInfo(bot);
                botsAux.Remove(bot["id"].ToString());
            }
        }
        // Los que queden en botsAux son los que hay que eliminar
        foreach (var botToRemove in botsAux)
        {
            logicaBots.EliminarBot(diccionarioBots, botToRemove.Key);
        }
    }
}
