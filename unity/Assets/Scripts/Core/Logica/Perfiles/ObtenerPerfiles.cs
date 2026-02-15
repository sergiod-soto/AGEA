using Newtonsoft.Json.Linq;
using TMPro;
using UnityEditor.PackageManager;
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
            Debug.Log("Perfil " + (i + 1) + ":\n" + perfiles[i].ToString());
            SetPerfil(perfilesGameObject[i], (JObject)perfiles[i]);
        }
    }

    void SetPerfil(GameObject perfilGameObject, JObject perfil)
    {
        if (perfil["fecha"].Equals(""))
        {
            // perfil NO creado
            perfilGameObject.transform.Find("Nombre").GetComponent<TextMeshProUGUI>().text = perfil["id"].ToString();
            perfilGameObject.transform.Find("Nuevo").gameObject.SetActive(true);
            perfilGameObject.transform.Find("Cargar").gameObject.SetActive(false);
        }
        else
        {
            // perfil que ya existe
            perfilGameObject.transform.Find("Nombre").GetComponent<TextMeshProUGUI>().text = perfil["nombre"].ToString();
            perfilGameObject.transform.Find("Nuevo").gameObject.SetActive(false);

            Transform cargar = perfilGameObject.transform.Find("Cargar");
            cargar.gameObject.SetActive(true);
            cargar.Find("Fecha Valor").GetComponent<TextMeshProUGUI>()
                .text = ParsearFecha(perfil["fecha"]);
            cargar.Find("Tiempo Entrenamiento Valor").GetComponent<TextMeshProUGUI>()
                .text = ParsearTiempo(perfil["tiempo"]);
        }
    }

    string ParsearFecha(JToken fecha)
    {
        return "2023-06-30";
        //return fecha.ToString();
    }

    string ParsearTiempo(JToken tiempo)
    {
        return "00:00:00";
        //return tiempo.ToString();
    }

}
