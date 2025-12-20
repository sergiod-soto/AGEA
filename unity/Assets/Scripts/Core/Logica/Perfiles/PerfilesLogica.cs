using Newtonsoft.Json.Linq;
using UnityEngine;

[RequireComponent(typeof(ObtenerPerfiles))]
[RequireComponent(typeof(CambiarPerfil))]
[RequireComponent(typeof(CambiarNombre))]
[RequireComponent(typeof(ObtenerInfoPerfilActivo))]
public class PerfilesLogica : MonoBehaviour, IPerfilesLogica
{
    void Start()
    {
        GetPerfiles();
    }

    public void GetPerfiles()
    {
        GetComponent<ObtenerPerfiles>().ObtenerListaPerfiles();
    }
    public void SetPerfilActivo(string perfil)
    {
        GetComponent<CambiarPerfil>().ChangeActiveProfile(perfil);
    }
    public void GetInfoPerfilActivo()
    {
        GetComponent<ObtenerInfoPerfilActivo>().ObtenerInfo();
    }
    public void CambiarNombrePerfilActivo(string nuevoNombre)
    {
        GetComponent<CambiarNombre>().ChangeName(nuevoNombre);
    }
}
