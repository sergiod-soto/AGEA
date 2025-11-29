using Newtonsoft.Json.Linq;
using UnityEngine;

public class DigestionMensajesPendientes : MonoBehaviour
{

    IConexionMundo conexionMundo;




    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    private void Update()
    {
        if (conexionMundo.GetMensajesPendientes().TryDequeue(out string mensaje))
        {
            //Debug.Log("Mensaje Unity -> Python:\n" + mensaje);
        }
    }
}
