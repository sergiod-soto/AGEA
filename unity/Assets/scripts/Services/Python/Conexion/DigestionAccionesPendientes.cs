using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using UnityEngine;

public class DigestionAccionesPendientes : MonoBehaviour, IProcesamientoEntradaConexion
{
    IConexionMundo conexionMundo;
    IBotsLogica logicaBots;

    public string entrada;



    // Start is called once before the first execution of Update after the MonoBehaviour is created
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
            case "":

                break;
        }



    }

    JObject Parsear(string entrada)
    {
        this.entrada = entrada;

        if (string.IsNullOrWhiteSpace(entrada))
        {
            this.entrada = "[entrada vacia]";
            return null;
        }
        try
        {
            // Parsear string a JObject (Newtonsoft.Json)
            return JObject.Parse(entrada);
        }
        catch (JsonReaderException jex)
        {
            Debug.LogError($"JSON inválido: {jex.Message} — entrada: {entrada}");
            // Si prefieres, encolar el texto crudo en MensajesPendientes para revisión
            conexionMundo?.MensajesPendientes?.Enqueue(entrada);
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error procesando entrada JSON: {ex}");
        }
        return null;
    }

}
