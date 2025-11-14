using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

public class main : MonoBehaviour
{

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {

    }

    // Update is called once per frame
    void Update()
    {
        ConcurrentQueue<JObject> accionesPendientesPython = GetComponent<ConexionMundo>().accionesPendientes;

        while (accionesPendientesPython.TryDequeue(out JObject data_from_python))
        {
            EjecutarServerTicBots(data_from_python);
        }

    }

    void EjecutarServerTicBots(JObject data)
    {
        JArray bots_data = (JArray)data["bots_data"]; // array de bots a actualizar
        //JArray bots_vivos = (JArray)data["bots_vivos"]; // array de ids de bots vivos

        Dictionary<string, GameObject> botsDict = GetComponent<Bots_gameobject_data>().bots_GameObjects; // dict de bots 
        Dictionary<string, GameObject> botsDictCopia = new(botsDict); // copia para detectar bots eliminados


        // hay que quitar las acciones sobre bots vivos
        //HashSet<string> bots_vivos_set = new();
        //for (int i = 0; i < bots_vivos.Count; i++)
        //{
        //    bots_vivos_set.Add(bots_vivos[i].ToString());
        //}

        for (int i = 0; i < bots_data.Count; i++)
        {
            // busco si el bot ya existe
            if (botsDict.ContainsKey(bots_data[i]["id"].ToString()))
            {
                // toca actualizarlo
                ActualizarBot((JObject)bots_data[i]);
                botsDictCopia.Remove(bots_data[i]["id"].ToString());
            }
            else
            {
                // toca crearlo
                GameObject bot = CrearBot((JObject)bots_data[i]);
                botsDict.Add(bot.GetComponent<bot_info>().id, bot);
            }
        }

        // puede que haya bots en botsDict que no hayan sido actualizados.
        // si aparecen en bots_vivos se dejan tranquilos, de los contrario, se eliminan
        //if (botsDictCopia.Count > 0)
        //{
        //    Dictionary<string, GameObject>.Enumerator ite = botsDictCopia.GetEnumerator();
        //    while (ite.MoveNext())
        //    {
        //        string k = ite.Current.Key;
        //        if (!bots_vivos_set.Contains(k))
        //        {
        //            // elimino el bot inexistente
        //            EliminarBot(botsDict, k);
        //        }

        //    }
        //}

        // Ejecutar otras acciones
        EjecutarOther((JObject)data["other"]);


        // tras crear/actualizar/eliminar bots, los renderizo
        GetComponent<renderizar_bots>().renderizarBots(botsDict);
    }

    GameObject CrearBot(JObject json)
    {
        GameObject bot = GetComponent<Generador_bot>().Create_bot(json);
        return bot;
    }

    void ActualizarBot(JObject new_bot)
    {
        GameObject old_bot = GetComponent<Bots_gameobject_data>().bots_GameObjects[new_bot["id"].ToString()];
        old_bot.GetComponent<bot_info>().ActualizarBot(new_bot);
    }


    void EliminarBot(Dictionary<string, GameObject> botsDict, string bot)
    {
        botsDict.Remove(bot);
    }



    void EjecutarOther(JObject other)
    {

    }

}
