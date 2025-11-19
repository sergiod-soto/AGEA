using UnityEngine;
using System.Diagnostics;
using UnityEditor;
using System.Collections;


public class BotonesMenuPrincipal : MonoBehaviour
{
    IDEVManager DEVManager;
    IConexionMundo conexionMundo;


    private Process pythonProcess;
    private Coroutine envioCoroutine;


    private void Start()
    {
        DEVManager = ServiceLocator.Instance.Get<IDEVManager>();
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {
        DEVManager.StartFakeServer();
        conexionMundo.Arrancar();

        // Inicia la coroutine que envía mensajes periódicos sin bloquear Unity
        //topEnviarMensajes(); // evita múltiples coroutines si se pulsa varias veces
        //envioCoroutine = StartCoroutine(EnviarMensajesPeriodicos(1.0f));
    }

    private IEnumerator EnviarMensajesPeriodicos(float intervaloSegundos)
    {
        int i = 0;
        var wait = new WaitForSeconds(intervaloSegundos);

        while (true)
        {
            // Envía el mensaje y espera sin bloquear el hilo principal
            conexionMundo.EnviarMensaje("i: " + i);
            i++;
            yield return wait;
        }
    }
    private void StopEnviarMensajes()
    {
        if (envioCoroutine != null)
        {
            StopCoroutine(envioCoroutine);
            envioCoroutine = null;
        }
    }

    public void Boton_Preferences()
    {
        print("Boton_Preferences");
    }

    public void Boton_Exit()
    {
        if (pythonProcess != null && !pythonProcess.HasExited)
        {
            pythonProcess.CloseMainWindow(); // primero, cierre limpio
            pythonProcess.WaitForExit(2000); // espera 2s

            if (!pythonProcess.HasExited)
                pythonProcess.Kill(); // si no se cierra, lo matamos

            pythonProcess.Dispose();
        }
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
    // Si el juego está compilado
    Application.Quit();
#endif
    }
}
