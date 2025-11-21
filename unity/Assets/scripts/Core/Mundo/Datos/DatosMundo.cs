using UnityEngine;

[RequireComponent(typeof(BotsDatos))]
public class DatosMundo : MonoBehaviour, IDatosMundo
{
    BotsDatos IDatosMundo.DatosBots => GetComponent<BotsDatos>();




}
