using UnityEngine;
using System.Diagnostics;


public class BotonesMenuPrincipal : MonoBehaviour
{

    private readonly Process pythonProcess;


    void Awake()
    {

    }

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {

    }


    public void Boton_Preferences()
    {
        UnityEngine.Debug.Log("Boton_Preferences");
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
