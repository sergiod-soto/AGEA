using UnityEngine;

public class funciones_botones_hud_start : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void Boton_Start()
    {

    }
    public void Boton_Preferences()
    {
        print("Boton_Preferences");
    }
    public void Boton_Exit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
    // Si el juego está compilado
    Application.Quit();
#endif
    }
}
