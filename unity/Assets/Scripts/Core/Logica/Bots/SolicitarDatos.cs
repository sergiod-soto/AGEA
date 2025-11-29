using TMPro;
using UnityEngine;

public class SolicitarDatos : MonoBehaviour
{
    IConexionMundo conexion;




    void Start()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }



    public void ClicEnBot(BotInfo bot_inf)
    {
        // toca pedir resto de datos a python    
        conexion.EnviarMensaje("{\"tipo\":\"dato\",\"entity\":\"bot\",\"id\":\"" + bot_inf.id + "\"}");
    }
}
