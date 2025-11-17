using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using UnityEngine;

public class bot_info : MonoBehaviour
{
    public string id;
    public (int x, int y) casilla;
    public int[] adn;
    public (bot_info padre, bot_info madre) padres;
    public string[] apellidos;
    public Dictionary<string, int> stats;
    public JObject datos_completos;

    public void SetStats(string id, (int x, int y) casilla, int[] adn,
        (bot_info padre, bot_info madre) padres, string[] apellidos,
        Dictionary<string, int> stats)
    {
        this.id = id;
        this.casilla = casilla;
        this.adn = adn;
        this.padres = padres;
        this.apellidos = apellidos;
        this.stats = stats;
    }

    public void ActualizarBot(JObject new_bot)
    {
        // Actualizar las propiedades del bot con los nuevos datos
        this.casilla = ((int)new_bot["casilla"]["x"], (int)new_bot["casilla"]["y"]);
        this.adn = new_bot["adn"].ToObject<int[]>();
        this.apellidos = new_bot["apellidos"].ToObject<string[]>();
        this.stats = new_bot["stats"].ToObject<Dictionary<string, int>>();
    }



    public string To_string()
    {
        // Ejemplo de serialización usando Newtonsoft.Json
        return JsonConvert.SerializeObject(this);
    }
}

