using Newtonsoft.Json.Linq;
using UnityEngine;

public class DigestionMensajesPendientes : MonoBehaviour
{
    IConexionMundo conexionMundo;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }
    void Update()
    {
        if (conexionMundo.GetMensajesPendientes().TryDequeue(out string mensaje))
        {
            //Debug.Log("Mensaje Unity -> Python:\n" + mensaje);
        }
    }
}
