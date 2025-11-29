using Newtonsoft.Json.Linq;
using NUnit.Framework;
using TMPro;
using UnityEngine;

public class SolicitarDatos : MonoBehaviour
{
    IConexionMundo conexion;
    IHUDRunningControl HUD_Running;

    public TextMeshProUGUI posicion_value;
    public TextMeshProUGUI id_value;
    public TextMeshProUGUI propiedades_value;
    public TextMeshProUGUI propiedades_avanzadas_value;
    public TextMeshProUGUI apellidos_value;


    void Start()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
        HUD_Running = ServiceLocator.Instance.Get<IHUDRunningControl>();
    }



    public void ClicEnBot(BotInfo bot_inf)
    {
        // toca pedir resto de datos a python    
        conexion.EnviarMensaje("{\"tipo\":\"dato\",\"entity\":\"bot\",\"id\":\"" + bot_inf.id + "\"}");
    }


    public void ActualizarHUD(JObject bot)
    {
        HUD_Running.Show_HUD();
        posicion_value.text = SerializarPosicionValue(bot);
        id_value.text = SerializarId(bot);
        propiedades_value.text = SerializarPropiedadesValue(bot);
        propiedades_avanzadas_value.text = SerializarPropiedadesAvanzadasValue(bot);
        apellidos_value.text = SerializarApellidosValue(bot);
    }

    string SerializarId(JObject bot)
    {
        return bot["id"].ToString();
    }
    string SerializarPosicionValue(JObject bot)
    {
        return bot["casilla"]["x"].ToString() + ", " + bot["casilla"]["y"].ToString();
    }
    string SerializarPropiedadesValue(JObject bot)
    {
        string[] unidades = new string[]{
            //          stat                 unidades
            bot["stats"]["vida"].ToString(),
            bot["stats"]["energia"].ToString(),
            bot["stats"]["curacion"].ToString() + "v/s",
            bot["stats"]["regeneracion"].ToString() + "e/s",
            bot["stats"]["velocidad"].ToString() + "m/s",
            bot["stats"]["atk"].ToString() + " daño",
            bot["stats"]["def"].ToString() + " defensa",
            bot["stats"]["deteccion"].ToString() + " lv",
            bot["stats"]["sigilo"].ToString() + " lv",
            bot["stats"]["edad"].ToString( )+ " días",
            bot["stats"]["edad_adulta"].ToString() + " días",
            bot["stats"]["temperatura"].ToString() + "ºC",
            bot["stats"]["regulacion_temperatura"].ToString() + "ºC/s"
        };

        string texto = unidades[0] +
                   "\r\n" + unidades[1] +
                   "\r\n" + unidades[2] +
                   "\r\n" + unidades[3] +
                   "\r\n" + unidades[4] +
                   "\r\n" + unidades[5] +
                   "\r\n" + unidades[6] +
                   "\r\n" + unidades[7] +
                   "\r\n" + unidades[8] +
                   "\r\n" + unidades[9] +
                   "\r\n" + unidades[10] +
                   "\r\n" + unidades[11] +
                   "\r\n" + unidades[12];

        return texto;
    }
    string SerializarPropiedadesAvanzadasValue(JObject bot)
    {
        string[] unidades = new string[]{
            //            stat                   unidades
            bot["stats"]["tamanho"].ToString(),
            bot["stats"]["grasa"].ToString(),
            bot["stats"]["movilidad"].ToString(),
            bot["stats"]["percepcion"].ToString(),
            bot["stats"]["armadura"].ToString(),
            bot["stats"]["metabolismo"].ToString(),
            bot["stats"]["agresividad"].ToString(),
            bot["stats"]["longevidad"].ToString() + " días",
            bot["stats"]["temperatura_optima"].ToString()+ "ºC"
        };

        string texto = unidades[0] +
                   "\r\n" + unidades[1] +
                   "\r\n" + unidades[2] +
                   "\r\n" + unidades[3] +
                   "\r\n" + unidades[4] +
                   "\r\n" + unidades[5] +
                   "\r\n" + unidades[6] +
                   "\r\n" + unidades[7] +
                   "\r\n" + unidades[8];

        return texto;
    }
    string SerializarApellidosValue(JObject bot)
    {

        return bot["apellidos"][0] + ", " +
            bot["apellidos"][1] + ", " +
            bot["apellidos"][2] + ", " +
            bot["apellidos"][3];
    }
}
