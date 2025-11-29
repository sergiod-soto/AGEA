using System.Collections.Generic;
using TMPro;
using UnityEngine;

[RequireComponent(typeof(BotInfo))]
public class BotClicked : MonoBehaviour
{





    public void OnClick()
    {
        string id = GetComponent<BotInfo>().id;

        Debug.Log("ID: " + id);
    }
}
