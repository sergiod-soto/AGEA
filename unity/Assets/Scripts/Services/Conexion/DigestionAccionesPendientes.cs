using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Concurrent;
using System.Threading;
using UnityEngine;

/*
 *      Clase encargada de procesar los mensajes entrantes del servidor python
 */

public class DigestionAccionesPendientes : MonoBehaviour, IProcesamientoEntradaConexion
{
    IConexionMundo conexionMundo;
    IBotsLogica logicaBots;


    void Start()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
        logicaBots = ServiceLocator.Instance.Get<IBotsLogica>();

    }

    public void DigerirEntrada(JObject json)
    {
        if (json == null)
        {
            return;
        }

        // Tras parsear, digerir segun tipo de mensaje
        switch (json["tipo"].ToString())
        {
            case "actualizacion":
                logicaBots.ActualizarBots((JArray)json["bots"]);
                break;
            case "dato":

                break;
        }



    }

    void Update()
    {
        //Debug.Log("count de acciones pendientes: " + conexionMundo.GetAccionesPendientes().Count);
        try
        {
            if (conexionMundo.GetAccionesPendientes().TryDequeue(out JObject json))
            {
                Debug.Log("entra a dequeue AccionesPendientes");
                DigerirEntrada(json);
            }
            else
            {
                Thread.Sleep(5); // evitar consumo de CPU
            }
        }
        catch (Exception ex)
        {
            Debug.Log("Error en el dequeue de DigestionAccionesPendientes:\n" + ex.Message);
        }
    }

}
