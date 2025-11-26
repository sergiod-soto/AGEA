
using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

public interface IService { }

public interface IConexionMundo : IService
{
    void Arrancar();
    void EnviarMensaje(string data);
    ConcurrentQueue<JObject> GetAccionesPendientes();
    ConcurrentQueue<string> GetMensajesPendientes();
}

public interface IBotsGameobjectData : IService
{
    Dictionary<string, GameObject> Bots_GameObjects { get; }
}

public interface IBotsLogica : IService
{
    public void OnClic();
    public GameObject CreateBot(JObject datos);
    public void ClicEnBot(BotInfo bot_inf);
    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject);
    public void ActualizarBots(JArray bots);

    public void EliminarBot(Dictionary<string, GameObject> diccionarioBots, string idBot);
}

public interface IGameLogica : IService
{
    public void ActivarActualizacionDatos();
    public void DesactivarActualizacionDatos();
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
    void DigerirEntrada(JObject data);
}

public interface IArrancarPythonService : IService
{
    Process ArrancarPython();
}
