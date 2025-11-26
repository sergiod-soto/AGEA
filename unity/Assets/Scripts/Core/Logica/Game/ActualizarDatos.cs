using System;
using System.Collections;
using UnityEngine;

public class ActualizarDatos : MonoBehaviour, IGameLogica
{
    IConexionMundo conexionMundo;

    public int intervaloMs;

    Coroutine rutina;
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
        rutina = StartCoroutine(EjecutarCadaXms());
    }

    public void DesactivarActualizacionDatos()
    {
        if (!activado) return;

        activado = false;

        if (rutina != null)
            StopCoroutine(rutina);
    }

    private IEnumerator EjecutarCadaXms()
    {
        float intervaloSeg = intervaloMs / 1000f;

        while (activado)
        {
            // mandamos peticion de actualizacion de datos
            conexionMundo.EnviarMensaje("{\"tipo\":\"actualizacion\"}");

            yield return new WaitForSeconds(intervaloSeg);
        }
    }

}
