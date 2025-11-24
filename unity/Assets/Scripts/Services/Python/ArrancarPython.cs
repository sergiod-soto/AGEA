using System.Diagnostics;
using UnityEngine;

public class ArrancarPythonClass : MonoBehaviour, IArrancarPythonService
{
    public Process ArrancarPython()
    {
        Process pythonProcess = new();
        pythonProcess.StartInfo.FileName = "../python/venv/Scripts/python.exe";
        pythonProcess.StartInfo.Arguments = "../python/Main.py";

        // Opcional
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
                UnityEngine.Debug.LogError("[PYTHON ERROR] " + args.Data.ToString());
        };

        pythonProcess.Start();
        pythonProcess.BeginOutputReadLine();
        pythonProcess.BeginErrorReadLine();

        UnityEngine.Debug.Log("Python iniciado con PID: " + pythonProcess.Id);

        return pythonProcess;
    }
}
