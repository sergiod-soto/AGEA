using System.Collections.Generic;
using UnityEngine;

public class RenderizarBots : MonoBehaviour
{
    IBotsGameobjectData botsGameobjectData;

    private void Start()
    {
        botsGameobjectData = ServiceLocator.Instance.Get<IBotsGameobjectData>();
    }

    public void Renderizar()
    {
        Dictionary<string, GameObject> bots_gameObject = botsGameobjectData.Bots_GameObjects;
        IEnumerator<string> keyEnumerator = botsGameobjectData.Bots_GameObjects.Keys.GetEnumerator();
        while (keyEnumerator.MoveNext())
        {
            BotInfo info = bots_gameObject[keyEnumerator.Current].GetComponent<BotInfo>();

            bots_gameObject[keyEnumerator.Current].transform.SetPositionAndRotation(
                new Vector3(info.casilla.x, info.casilla.y, 0f),    // Posicion
                Quaternion.Euler(0f, 0f, info.rotacion));           // Rotacion
        }
    }
}
