using System.IO;
using UnityEngine;

public class CargaMascaras : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        string rutaRelativa = Path.Combine(Application.dataPath, "../../python/Core/Mundo/Mascaras");
        string rutaBase = Path.GetFullPath(rutaRelativa);


        if (File.Exists(rutaBase + "/desiertos.png"))
        {
            string contenido = File.ReadAllText(rutaBase + "/desiertos.png");
        }
        else
        {
            Debug.LogError("No se encontró el fichero: " + rutaBase);
        }
    }


}
