using UnityEngine;

public class DEV : MonoBehaviour, IDEVManager
{

    public void StartFakeServer()
    {
        // quiero que cuando le de al boton start, se inicie el servidor falso
        GetComponent<ServidorFalso>().Arrancar_Servidor_Falso();
    }


}
