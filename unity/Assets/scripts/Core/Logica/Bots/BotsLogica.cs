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
    void Awake()
    {
        var digestion = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();
        digestion.RegistrarHandler("actualizacion", json => ActualizarBots((JArray)json["bots"]));
        digestion.RegistrarHandler("dato", json => ActualizarHUDDatosBot((JObject)json["bot"]));
    }

    public GameObject CreateBot(JObject datos) => GetComponent<GeneradorBot>().CreateBot(datos);
    public void ClicEnBot(GameObject bot) => GetComponent<SolicitarDatos>().ClicEnBot(bot);
    public void ActualizarHUDDatosBot(JObject bot) => GetComponent<SolicitarDatos>().ActualizarHUD(bot);
    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject) => GetComponent<RenderizarBots>().Renderizar();
    public void ActualizarBots(JArray bots) => GetComponent<ActualizarBots>().ActualizarBotsMetodo(bots);
    public void EliminarBot(Dictionary<string, GameObject> diccionarioBots, string id) => GetComponent<EliminarBot>().EliminarBotMetodo(diccionarioBots, id);
}