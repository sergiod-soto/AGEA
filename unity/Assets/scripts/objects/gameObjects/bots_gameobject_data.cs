using System.Collections.Generic;
using UnityEngine;

public class Bots_gameobject_data : MonoBehaviour
{
    public Dictionary<string, GameObject> bots_GameObjects;

    private void Start()
    {
        bots_GameObjects = new Dictionary<string, GameObject>();
    }
}
