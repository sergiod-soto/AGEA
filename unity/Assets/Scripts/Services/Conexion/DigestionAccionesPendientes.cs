using Newtonsoft.Json.Linq;
using System;
using System.Threading;
using UnityEngine;

/*
 *      Clase encargada de procesar los mensajes entrantes del servidor python
 */

public class DigestionAccionesPendientes : MonoBehaviour, IProcesamientoEntradaConexion
{
    IConexionMundo conexionMundo;
    IBotsLogica logicaBots;
    IPerfilesLogica logicaPerfiles;

    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
        logicaBots = ServiceLocator.Instance.Get<IBotsLogica>();
        logicaPerfiles = ServiceLocator.Instance.Get<IPerfilesLogica>();
    }

    public void DigerirEntrada(JObject json)
    {
        if (json == null)
        {
            return;
        }

        // Tras parsear, digerir segun tipo de mensaje
        switch (json["peticion"].ToString())
        {
            case "actualizacion":
                logicaBots.ActualizarBots((JArray)json["bots"]);
                break;
            case "dato":
                logicaBots.ActualizarHUDDatosBot((JObject)json["bot"]);
                break;
            case "perfil":
                logicaPerfiles.SetPerfilesPantallaSeleccionPerfil((JArray)json["perfiles"]);
                break;
        }
    }

    void Update()
    {
        try
        {
            if (conexionMundo.GetAccionesPendientes().TryDequeue(out JObject json))
            {
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
