using System.Collections.Generic;
using UnityEngine;

public class renderizar_bots : MonoBehaviour
{

    public void renderizarBots(Dictionary<string, GameObject> bots_gameObject)
    {       
        IEnumerator<string> k = GetComponent<Bots_gameobject_data>().bots_GameObjects.Keys.GetEnumerator();
        while (k.MoveNext())
        {
            bots_gameObject[k.Current].transform.position = new Vector3(
                bots_gameObject[k.Current].GetComponent<bot_info>().casilla.x,
                bots_gameObject[k.Current].GetComponent<bot_info>().casilla.y,
                0f);
        }
    }
}
