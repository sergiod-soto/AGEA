using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;


public class GeneradorBot : MonoBehaviour
{
    IDatosMundo datosMundo;
    IBotsLogica logicaBots;

    public GameObject bot_preinstanciado;
    public GameObject carpeta_instancias;

    private void Awake()
    {
        datosMundo = ServiceLocator.Instance.Get<IDatosMundo>();
        logicaBots = ServiceLocator.Instance.Get<IBotsLogica>();
    }

    public GameObject CreateBot(JObject datos)
    {
        if (datos == null) return null;

        int tamanho = (int)datos["tamanho"];
        int x = (int)datos["casilla"]["x"];
        int y = (int)datos["casilla"]["y"];
        float rotacion = (float)datos["rotacion"];

        GameObject bot = Instantiate(bot_preinstanciado, new Vector3(x, y, 0), Quaternion.Euler(0, 0, rotacion), carpeta_instancias.transform);
        bot.GetComponent<BotInfo>().SetStats(datos["id"].ToString(), tamanho, (x, y), rotacion);
        datosMundo.DatosBots.Bots_GameObjects.Add(datos["id"].ToString(), bot);

        return bot;
    }
}



