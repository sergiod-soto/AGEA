using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.UI;

public class SolicitarPerfiles : MonoBehaviour
{
    public GameObject perfil1;
    public GameObject perfil2;
    public GameObject perfil3;
    public GameObject perfil4;
    public GameObject perfil5;
    public GameObject perfil6;

    IConexionMundo conexion;
    private void Awake()
    {
        conexion = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    public void SolicitarListaPerfiles()
    {
        conexion.EnviarMensaje("{\"peticion\":\"perfil\",\"tipo\":\"obtener_perfiles\"}");
    }

    public void SetPerfilesPantallaSeleccionPerfil(JArray perfiles)
    {
        GameObject[] perfilesGameObject = { perfil1, perfil2, perfil3, perfil4, perfil5, perfil6 };

        for (int i = 0; i < perfiles.Count; i++)
        {
            SetPerfil(perfilesGameObject[i], (JObject)perfiles[i]);
        }
    }

    void SetPerfil(GameObject perfilGameObject, JObject perfil)
    {
        if (perfil["fecha"].Equals(""))
        {
            // perfil NO creado
            perfilGameObject.transform.Find("Nombre").GetComponent<Text>().text = perfil["id"].ToString();
            perfilGameObject.transform.Find("Nuevo").gameObject.SetActive(true);
            perfilGameObject.transform.Find("Cargar").gameObject.SetActive(false);
        }
        else
        {
            // perfil que ya existe
            perfilGameObject.transform.Find("Nombre").GetComponent<Text>().text = perfil["nombre"].ToString();
            perfilGameObject.transform.Find("Nuevo").gameObject.SetActive(false);
            perfilGameObject.transform.Find("Cargar").gameObject.SetActive(true);
            perfilGameObject.transform.Find("Cargar")
                .Find("Fecha Texto").GetComponent<Text>().text = perfil["fecha"].ToString();
            perfilGameObject.transform.Find("Cargar")
                .Find("Tiempo Entrenamiento").GetComponent<Text>().text = perfil["tiempo"].ToString();
        }
    }

}
