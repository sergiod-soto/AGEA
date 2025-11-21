using UnityEngine;

[RequireComponent(typeof(ServidorFalsoPython))]
public class DEV : MonoBehaviour, IDEVManager
{

    public void StartFakeServer()
    {
        // quiero que cuando le de al boton start, se inicie el servidor falso
        GetComponent<ServidorFalsoPython>().Arrancar_Servidor_Falso();
    }

    public void Test()
    {
        GetComponent<Pruebas>().Test();
    }


}
