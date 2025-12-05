using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class CargarMapas : MonoBehaviour
{

    public string direccionBaseMascaras;

    string rutaBase;
    string[] ficheros;

    void Awake()
    {
        string rutaRelativa = Path.Combine(Application.dataPath, direccionBaseMascaras);
        rutaBase = Path.GetFullPath(rutaRelativa);

        ficheros = new[]{
            "/desiertos.png",
          
        };

    }

    void CargarMapa()
    {

    }

    public void CargarMapasMetodo(Dictionary<string, int[,]> mapas)
    {
        throw new System.NotImplementedException();
    }

    public bool ComprobarMapas()
    {
        foreach (string fichero in ficheros)
        {
            if (!File.Exists(rutaBase + fichero))
            {
                Debug.Log("No se ha encontrado mascara válida en: " + fichero);
                return false;
            }
        }
        return true;
    }
}
