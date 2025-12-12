using UnityEngine;
using System.Diagnostics;
using System.Collections;


public class BotonesMenuPrincipal : MonoBehaviour
{
    IConexionMundo conexionMundo;
    IGameLogica logicaJuego;
    IControlHUDLogica logicaHUD;


    private readonly Process pythonProcess;


    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
        logicaJuego = ServiceLocator.Instance.Get<IGameLogica>();
        logicaHUD = ServiceLocator.Instance.Get<IControlHUDLogica>();
    }

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {
        //DEVManager.StartFakeServer();
        conexionMundo.Arrancar();
        logicaJuego.ActivarActualizacionDatos();
        logicaHUD.StartGame();
    }


    public void Boton_Preferences()
    {
        logicaHUD.EnterOptions();
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
