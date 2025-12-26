using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(CargarMapas))]
public class MapaLogica : MonoBehaviour, IMapaLogica
{
    public void CargarMapas(Dictionary<string, int[,]> mapas)
    {
        GetComponent<CargarMapas>().CargarMapasMetodo(mapas);
    }

    public bool ComprobarMapas()
    {
        return GetComponent<CargarMapas>().ComprobarMapas();
    }

    public void SolicitarMapas()
    {
        throw new System.NotImplementedException();
    }
}
