using System.Collections.Generic;
using TMPro;
using UnityEngine;

[RequireComponent(typeof(BotInfo))]
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
        string id = GetComponent<BotInfo>().id;

        Debug.Log("ID: " + id);
    }
}
