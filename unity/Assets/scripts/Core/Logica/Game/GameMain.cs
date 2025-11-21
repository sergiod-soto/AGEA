using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

public class GameMain : MonoBehaviour
{
    IConexionMundo conexion;
    IBotsLogica botsLogica;
    IDatosMundo datosMundo;
    IProcesamientoEntradaConexion procesamientoEntradaConexion;
    IBotsGameobjectData botsGameobjectData;



    private void Start()
    {
        datosMundo = ServiceLocator.Instance.Get<IDatosMundo>();
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
        botsLogica = ServiceLocator.Instance.Get<IBotsLogica>();
        procesamientoEntradaConexion = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();
        botsGameobjectData = ServiceLocator.Instance.Get<IBotsGameobjectData>();
    }

    // Update is called once per frame
    void Update()
    {
        ConcurrentQueue<JObject> accionesPendientesPython = conexion.AccionesPendientes;

        while (accionesPendientesPython.TryDequeue(out JObject dataFromPython))
        {
            EjecutarServerTicBots(dataFromPython);
        }

    }

    void EjecutarServerTicBots(JObject data)
    {
        procesamientoEntradaConexion.DigerirEntrada(data);
        botsLogica.RenderizarBots(botsGameobjectData.Bots_GameObjects);
    }
}
