
using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

public interface IService { }

public interface IConexionMundo : IService
{
    ConcurrentQueue<JObject> AccionesPendientes { get; }
    ConcurrentQueue<string> MensajesPendientes { get; }
    void Arrancar();
    void EnviarMensaje(string data);

}

public interface IBotsGameobjectData : IService
{
    Dictionary<string, GameObject> Bots_GameObjects { get; }
}

public interface IBotsLogica : IService
{
    public void OnClic();
    public GameObject CreateBot(JObject datos);
    public void ClicEnBot(bot_info bot_inf);
    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject);
}

public interface IMundo : IService
{
    void RenderizarBots(Dictionary<string, GameObject> bots_gameObject);
}

public interface IDatosMundo : IService
{
    BotsDatos DatosBots { get; }
}

public interface IDEVManager : IService
{
    void StartFakeServer();
    void Test();
}

public interface IProcesamientoEntradaConexion : IService
{
    void DigerirEntrada(string entrada);
}


