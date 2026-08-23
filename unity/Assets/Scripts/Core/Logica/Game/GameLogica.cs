using UnityEngine;

[RequireComponent(typeof(Pausar))]
public class GameLogica : MonoBehaviour
{
    public void PausarSimulacion()
    {
        GetComponent<Pausar>().PausePython();
    }
}