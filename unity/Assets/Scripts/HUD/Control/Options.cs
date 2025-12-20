using UnityEngine;

[RequireComponent(typeof(ControlHUD))]
public class Options : MonoBehaviour
{
    GameObject HUDBase;
    void Start()
    {
        HUDBase = GetComponent<ControlHUD>().HUDBase;
    }

    /*
     * entramos en preferences
     */
    public void EnterOptions()
    {
        throw new System.NotImplementedException();
    }

    /*
    * al cerrar las opciones
    */
    public void ExitOptions()
    {
        throw new System.NotImplementedException();
    }

}
