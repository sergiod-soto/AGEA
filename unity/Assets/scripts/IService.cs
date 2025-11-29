
using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

/*
 *      Base. ServiceLocatos busca todas las interfaces que implementan esta interfaz. 
 *      
 *      En caso de haber mas de una (2 scripts implementando la misma interfaz o 
 *      dos objetos con el mismo script), da error.
 */
public interface IService { }

/*
 *      Se encarga de conectar via TCP/IP con el script de Python
 */
public interface IConexionMundo : IService
{
    void Arrancar();
    void EnviarMensaje(string data);
    ConcurrentQueue<JObject> GetAccionesPendientes();
    ConcurrentQueue<string> GetMensajesPendientes();
}


/*
 *      Almacena los GameObject de los bots
 */
public interface IBotsGameobjectData : IService
{
    Dictionary<string, GameObject> Bots_GameObjects { get; }
}


/*
 *      Logica de interaccion de los bots como conjunto
 */
public interface IBotsLogica : IService
{
    public GameObject CreateBot(JObject datos);
    public void ClicEnBot(BotInfo bot_inf);
    public void RenderizarBots(Dictionary<string, GameObject> bots_gameObject);
    public void ActualizarBots(JArray bots);
    public void ActualizarHUDDatosBots(JObject bot);
    public void EliminarBot(Dictionary<string, GameObject> diccionarioBots, string idBot);

}

/*
 *      Control general del juego
 */
public interface IGameLogica : IService
{
    public void ActivarActualizacionDatos();
    public void DesactivarActualizacionDatos();

    public void PausarSimulacion();
}

/*
 *      Control visual del mundo
 */
public interface IMundo : IService
{
    void RenderizarBots(Dictionary<string, GameObject> bots_gameObject);
}

/*
 *      Datos de los bots como informacion, no como objeto
 */
public interface IDatosMundo : IService
{
    BotsDatos DatosBots { get; }
}

/*
 *      Testing
 */
public interface IDEVManager : IService
{
    void StartFakeServer();
    void Test();
}

/*
 *      Que se hace con los mensajes que llegan desde Python
 */
public interface IProcesamientoEntradaConexion : IService
{
    void DigerirEntrada(JObject data);
}

/*
 *      Se encarga de arrancar el script Python
 */
public interface IArrancarPythonService : IService
{
    Process ArrancarPython();
}

/*
 * 
 */
public interface IHUDRunningControl : IService
{
    public void Show_HUD();
    public void Hide_HUD();
}
