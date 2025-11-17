using UnityEngine;

public class DatosMundo : MonoBehaviour, IDatosMundo
{
    BotsDatos IDatosMundo.DatosBots => GetComponent<BotsDatos>();




}
