using System;
using System.Collections;
using UnityEngine;

public class ActualizarDatos : MonoBehaviour
{
    IConexionMundo conexionMundo;

    public int intervaloMs;

    float acumulador = 0f;
    bool activado;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        activado = false;
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }


    public void ActivarActualizacionDatos()
    {
        if (activado) return;

        activado = true;
    }

    public void DesactivarActualizacionDatos()
    {
        if (!activado) return;

        activado = false;
    }


    void Update()
    {
        acumulador += Time.deltaTime * 1000f; // lo pasamos a milisegundos

        if (acumulador >= intervaloMs && activado)
        {
            acumulador = 0f;

            // mandamos peticion de actualizacion de datos
            conexionMundo.EnviarMensaje("{\"tipo\":\"actualizacion\"}");
        }
    }
}
