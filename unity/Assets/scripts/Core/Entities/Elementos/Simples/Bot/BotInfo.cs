using Newtonsoft.Json.Linq;
using UnityEngine;

public class BotInfo : MonoBehaviour
{
    public string id;
    int tamanho;
    public (int x, int y) casilla;
    public float rotacion;


    public void SetStats(string id, int tamanho, (int x, int y) casilla, float rotacion)
    {
        this.id = id;
        this.tamanho = tamanho;
        this.casilla = casilla;
        this.rotacion = rotacion;
    }

    public void SetRotacion(float grados)
    {
        this.rotacion = grados;
    }

    public void ActualizarInfo(JObject new_bot)
    {
        // Actualizar las propiedades del bot con los nuevos datos
        this.casilla = ((int)new_bot["casilla"]["x"], (int)new_bot["casilla"]["y"]);
        this.rotacion = (float)new_bot["rotacion"];
    }



    public string To_string()
    {
        return "ID: " + id + ",\nCasilla: (" + casilla.x + ", " + casilla.y + "),\nRotacion: " + rotacion + "º";
    }
}

