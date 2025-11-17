using System.Collections.Generic;
using UnityEngine;

public class BotsDatos : MonoBehaviour, IBotsGameobjectData
{
    public Dictionary<string, GameObject> Bots_GameObjects;

    Dictionary<string, GameObject> IBotsGameobjectData.Bots_GameObjects => Bots_GameObjects;

    private void Start()
    {
        Bots_GameObjects = new();
    }
}
