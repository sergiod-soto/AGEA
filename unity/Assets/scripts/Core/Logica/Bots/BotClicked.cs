using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class BotClicked : MonoBehaviour
{

    public TextMeshProUGUI id_value;
    public TextMeshProUGUI propiedades_value;
    public TextMeshProUGUI propiedades_unidades;
    public TextMeshProUGUI propiedades_avanzadas_value;
    public TextMeshProUGUI propiedades_avanzadas_unidades;
    public TextMeshProUGUI apellidos_value;

    public void OnClick()
    {
        Debug.Log($"Clic en: {gameObject.name}");

        Dictionary<string, int> stats = GetComponent<bot_info>().stats;
        if (stats == null)
        {
            Debug.Log("stats == null");
        }
        else
        {
            Debug.Log("Nº llaves: " + stats.Keys.Count);
            foreach (string clave in stats.Keys)
            {
                Debug.Log("Clave: " + clave + ", valor: " + stats[clave]);
            }
        }
    }
}
