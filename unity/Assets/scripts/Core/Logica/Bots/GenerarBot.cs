using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;


public class GeneradorBot : MonoBehaviour
{
    IDatosMundo datosMundo;



    public GameObject bot_preinstanciado;
    public GameObject carpeta_instancias;


    private void Start()
    {
        datosMundo = ServiceLocator.Instance.Get<IDatosMundo>();
    }


    public GameObject CreateBot(JObject datos)
    {
        int x = (int)datos["casilla"]["x"];
        int y = (int)datos["casilla"]["y"];

        GameObject bot = Instantiate(bot_preinstanciado, new Vector3(x, y, 0), Quaternion.identity, carpeta_instancias.transform);

        if (datos != null)
        {
            (bot_info, bot_info) padres = (null, null);

            if (datos["padres"] == null)
            {
                Debug.LogError("ERROR GRAVE: 'datos[\"padres\"]' ES NULL EN Create_bot");
                throw new System.Exception("ERROR GRAVE: 'datos[\"padres\"]' ES NULL EN Create_bot, datos: " + datos.ToString());
            }
            if (datos["padres"]["padre"] == null || datos["padres"]["madre"] == null)
            {
                Debug.LogError("ERROR GRAVE: 'datos[\"padres\"][\"padre/madre\"]' ES NULL EN Create_bot");
                throw new System.Exception("ERROR GRAVE: 'datos[\"padres\"][\"padre/madre\"]' ES NULL EN Create_bot");

            }

            if (datos["padres"]["padre"].ToString() != "" && datos["padres"]["madre"].ToString() != "")
            {
                try
                {
                    padres = (datosMundo.DatosBots.Bots_GameObjects[datos["padres"]["padre"].ToString()]
                           .GetComponent<bot_info>(),
                      datosMundo.DatosBots.Bots_GameObjects[datos["padres"]["madre"].ToString()]
                           .GetComponent<bot_info>()
                   );
                }
                catch (KeyNotFoundException) { }
                catch (System.Exception) { Debug.LogError("ERROR GRAVE TRAYENDO 'Bot_info' DE PADRES "); }
            }


            string[] e = datos["apellidos"].ToObject<string[]>();

            Dictionary<string, int> f = datos["stats"].ToObject<Dictionary<string, int>>();

            bot_info info = bot.GetComponent<bot_info>();
            info.SetStats(
                datos["id"].ToString(), // id
                (x, y),                 // casilla
                datos["adn"].ToString() != "None" ? datos["adn"].ToObject<int[]>() : null, // adn
                padres,
                e,
                f
            );
            bot.SetActive(true);

            return bot;
        }
        else
        {
            // en principio, solo no tienen stats los bots creados para el debug
            // asignar stats por defecto
            bot.GetComponent<bot_info>().SetStats(
               "dev",
               (20, 0),
               new int[] { 0 },
               (null, null),
               new string[] { "apellido dev 1", "apellido dev 2" },
               new Dictionary<string, int> { }
           );
            bot.SetActive(true);
            return bot;
        }
    }
}



