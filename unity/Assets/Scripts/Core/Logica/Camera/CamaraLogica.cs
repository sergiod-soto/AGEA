using UnityEngine;

[RequireComponent(typeof(SeguirMovimientoGameObject))]
public class CamaraLogica : MonoBehaviour
{
    public void SeguirConCamara(GameObject newTarget)
    {
        GetComponent<SeguirMovimientoGameObject>().SeguirConCamara(newTarget);
    }
    public void DejarDeSeguirConCamara()
    {
        GetComponent<SeguirMovimientoGameObject>().DejarDeSeguirConCamara();
    }
}
