using Newtonsoft.Json.Linq;
using UnityEngine;

[RequireComponent(typeof(SolicitarPerfiles))]
[RequireComponent(typeof(CambiarPerfil))]
[RequireComponent(typeof(CambiarNombre))]
[RequireComponent(typeof(SolicitarInfoPerfilActivo))]
public class PerfilesLogica : MonoBehaviour, IPerfilesLogica
{
    void Start()
    {
        SolicitarPerfiles();
    }

    public void SolicitarPerfiles()
    {
        GetComponent<SolicitarPerfiles>().SolicitarListaPerfiles();
    }
    public void SetPerfilActivo(string perfil)
    {
        GetComponent<CambiarPerfil>().ChangeActiveProfile(perfil);
    }
    public void SolicitarInfoPerfilActivo()
    {
        GetComponent<SolicitarInfoPerfilActivo>().SolicitarInfo();
    }
    public void CambiarNombrePerfilActivo(string nuevoNombre)
    {
        GetComponent<CambiarNombre>().ChangeName(nuevoNombre);
    }
}
