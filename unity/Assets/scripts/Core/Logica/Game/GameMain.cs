using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

public class GameMain : MonoBehaviour
{
    IConexionMundo conexion;
    IBotsLogica botsLogica;
    IProcesamientoEntradaConexion procesamientoEntradaConexion;
    IBotsGameobjectData botsGameobjectData;



    void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
        botsLogica = ServiceLocator.Instance.Get<IBotsLogica>();
        procesamientoEntradaConexion = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();
        botsGameobjectData = ServiceLocator.Instance.Get<IBotsGameobjectData>();
    }

    // Update is called once per frame
    void Update()
    {
        ConcurrentQueue<JObject> accionesPendientesPython = conexion.GetAccionesPendientes();

        while (accionesPendientesPython.TryDequeue(out JObject dataFromPython))
        {
            EjecutarServerTicBots(dataFromPython);
        }

    }

    void EjecutarServerTicBots(JObject data)
    {
        Debug.Log("PRE DigerirEntrada");
        Debug.Log("data:\n" + data);

        procesamientoEntradaConexion.DigerirEntrada(data);
        Debug.Log("POST DigerirEntrada");
        botsLogica.RenderizarBots(botsGameobjectData.Bots_GameObjects);
    }
}
