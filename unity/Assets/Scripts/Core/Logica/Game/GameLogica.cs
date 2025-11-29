using UnityEngine;

[RequireComponent(typeof(Pausar))]
[RequireComponent(typeof(ActualizarDatos))]
public class GameLogica : MonoBehaviour, IGameLogica
{

    public void ActivarActualizacionDatos()
    {
        GetComponent<ActualizarDatos>().ActivarActualizacionDatos();
    }

    public void DesactivarActualizacionDatos()
    {
        GetComponent<ActualizarDatos>().DesactivarActualizacionDatos();
    }

    public void PausarSimulacion()
    {
        GetComponent<Pausar>().PausePython();
    }


}
