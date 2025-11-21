using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem.HID;

public class ObtenerDatos : MonoBehaviour
{
    public TextMeshProUGUI id_value;
    public TextMeshProUGUI posicion_value;
    public TextMeshProUGUI propiedades_text;
    public TextMeshProUGUI propiedades_value;
    public TextMeshProUGUI propiedades_unidades;
    public TextMeshProUGUI propiedades_avanzadas_text;
    public TextMeshProUGUI propiedades_avanzadas_value;
    public TextMeshProUGUI propiedades_avanzadas_unidades;
    public TextMeshProUGUI apellidos_value;
    public GameObject HUD;
    public GameObject showHUD;

    public void ClicEnBot(BotInfo bot_inf)
    {
        //Dictionary<string, int> stats = bot_inf.stats;
        //try
        //{
        //    HUD.SetActive(true);
        //    showHUD.SetActive(true);
        //    id_value.text = bot_inf.id;

        //    posicion_value.text = bot_inf.casilla.x + ", " + bot_inf.casilla.y;

        //    propiedades_text.text = "" +
        //        "Vida\n" +
        //        "Energia\n" +
        //        "Curación\n" +
        //        "Regeneración\n" +
        //        "Velocidad\n" +
        //        "Ataque\n" +
        //        "Defensa\n" +
        //        "Detección\n" +
        //        "Sigilo\n" +
        //        "Edad\n" +
        //        "Temperatura";

        //    propiedades_value.text = $"" +
        //        $"{stats["vida"]}\n" +
        //        $"{stats["energia"]}\n" +
        //        $"{stats["curacion"]}\n" +
        //        $"{stats["regeneracion"]}\n" +
        //        $"{stats["velocidad"]}\n" +
        //        $"{stats["atk"]}\n" +
        //        $"{stats["def"]}\n" +
        //        $"{stats["deteccion"]}\n" +
        //        $"{stats["sigilo"]}\n" +
        //        $"{stats["edad"]}\n" +
        //        $"{stats["temperatura"]}";

        //    propiedades_unidades.text = $"" +
        //        $"\n" +
        //        $"\n" +
        //        $"/s\n" +
        //        $"/s\n" +
        //        $" m/s\n" +
        //        $"\n" +
        //        $"\n" +
        //        $"\n" +
        //        $"\n" +
        //        $" Años\n" +
        //        $" ºC\n";

        //    propiedades_avanzadas_text.text = "" +
        //        "Edad Adulta\n" +
        //        "Regulacion Temperatura\n" +
        //        "Temperatura Óptima\n" +
        //        "Tamaño\n" +
        //        "Grasa\n" +
        //        "Movilidad\n" +
        //        "Armadura\n" +
        //        "Percepción\n" +
        //        "Metabolismo\n";

        //    propiedades_avanzadas_value.text = $"" +
        //        $"{stats["edad_adulta"]}\n" +
        //        $"{stats["regulacion_temperatura"]}\n" +
        //        $"{stats["temperatura_optima"]}" +
        //        $"{stats["tamanho"]}\n" +
        //        $"{stats["grasa"]}\n" +
        //        $"{stats["movilidad"]}\n" +
        //        $"{stats["percepcion"]}\n" +
        //        $"{stats["armadura"]}\n" +
        //        $"{stats["metabolismo"]}\n" +
        //        $"{stats["agresividad"]}\n";

        //    propiedades_avanzadas_unidades.text = "" +
        //        "" +
        //        "";

        //    string ape = "";
        //    for (int i = 0; i < bot_inf.apellidos.Length - 1; i++)
        //    {
        //        ape += Apellidos.apellidos[int.Parse(bot_inf.apellidos[i])] + ",\n";
        //    }
        //    ape += Apellidos.apellidos[int.Parse(bot_inf.apellidos[bot_inf.apellidos.Length - 1])] + "\n";
        //    apellidos_value.text = ape;

        //    return;
        //}
        //catch (Exception e)
        //{
        //    Debug.Log("Error obteniendo datos del bot, error: " + e.ToString());
        //}
    }
}
