using System.Collections.Generic;
using UnityEngine;

public class RenderizarBots : MonoBehaviour
{
    IBotsGameobjectData botsGameobjectData;

    private void Start()
    {
        botsGameobjectData = ServiceLocator.Instance.Get<IBotsGameobjectData>();
    }

    public void Renderizar(Dictionary<string, GameObject> bots_gameObject)
    {
        IEnumerator<string> k = botsGameobjectData.Bots_GameObjects.Keys.GetEnumerator();
        while (k.MoveNext())
        {
            bot_info info = bots_gameObject[k.Current].GetComponent<bot_info>();
            bots_gameObject[k.Current].transform.position = new Vector3(info.casilla.x, info.casilla.y, 0f);
        }
    }
}
