using UnityEngine;
using System.Diagnostics;
using System.Collections;


public class BotonesMenuPrincipal : MonoBehaviour
{
    IDEVManager DEVManager;
    IConexionMundo conexionMundo;
    IGameLogica logicaJuego;


    private Process pythonProcess;
    private Coroutine envioCoroutine;


    private void Start()
    {
        DEVManager = ServiceLocator.Instance.Get<IDEVManager>();
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
        logicaJuego = ServiceLocator.Instance.Get<IGameLogica>();

    }

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {
        //DEVManager.StartFakeServer();
        conexionMundo.Arrancar();
        logicaJuego.ActivarActualizacionDatos();
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
