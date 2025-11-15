using UnityEngine;
using System.Diagnostics;

public class funciones_botones_hud_start : MonoBehaviour
{
    private Process pythonProcess;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {
        pythonProcess = new Process();
        pythonProcess.StartInfo.FileName = "python"; // o ruta absoluta
        pythonProcess.StartInfo.Arguments = "../python/Main.py";

        // Opcional pero MUY recomendable
        pythonProcess.StartInfo.UseShellExecute = false;
        pythonProcess.StartInfo.RedirectStandardOutput = true;
        pythonProcess.StartInfo.RedirectStandardError = true;
        pythonProcess.StartInfo.CreateNoWindow = true;

        pythonProcess.OutputDataReceived += (sender, args) =>
        {
            if (!string.IsNullOrEmpty(args.Data))
                UnityEngine.Debug.Log("[PYTHON] " + args.Data);
        };
        pythonProcess.ErrorDataReceived += (sender, args) =>
        {
            if (!string.IsNullOrEmpty(args.Data))
                UnityEngine.Debug.LogError("[PYTHON ERROR] " + args.Data);
        };

        pythonProcess.Start();
        pythonProcess.BeginOutputReadLine();
        pythonProcess.BeginErrorReadLine();

        UnityEngine.Debug.Log("Python iniciado con PID: " + pythonProcess.Id);
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
