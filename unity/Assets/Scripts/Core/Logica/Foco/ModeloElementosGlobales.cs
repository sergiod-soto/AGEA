// Assets/Scripts/Core/Logica/Foco/ModeloElementosGlobales.cs
using System.Collections.Generic;
using System.Text;
using Newtonsoft.Json.Linq;
using UnityEngine;
using ComunicacionRemota;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Modelo GENÉRICO para ActualizacionFoco.elementos_globales (clima,
    /// ciclo lunar, etc.).
    ///
    /// PENDIENTE: en el ejemplo real que se usó para diseñar este módulo,
    /// 'elementos_globales' salió vacío (clima.py y ciclo_lunar.py aún no
    /// implementados del lado Python), así que no hay forma de saber hoy
    /// qué campos trae el 'state' (JSON de elem.to_snapshot()) de cada
    /// uno. Por eso se guarda como JObject genérico por nombre.
    ///
    /// Cuando existan ejemplos reales de 'state' para clima/ciclo lunar,
    /// esto debería reemplazarse por clases tipadas (ClimaEstado,
    /// CicloLunarEstado...) igual que se hizo con ElementoCelda, en vez
    /// de que cada consumidor lea el JObject a mano. No lo tipo ahora
    /// para no inventar campos que no he visto.
    /// </summary>
    public class ModeloElementosGlobales : MonoBehaviour
    {
        private IFocoStream _receptor;

        private readonly Dictionary<string, JObject> _estado = new();

        public bool TryObtener(string nombre, out JObject estado) =>
            _estado.TryGetValue(nombre, out estado);

        private void Awake() => _receptor = ServiceLocator.Instance.Get<IFocoStream>();

        private void OnEnable() => _receptor.OnActualizacionRecibida += Procesar;
        private void OnDisable() => _receptor.OnActualizacionRecibida -= Procesar;

        private void Procesar(ActualizacionFoco actualizacion)
        {
            if (!actualizacion.Ok) return;

            _estado.Clear();
            foreach (var elementoGlobal in actualizacion.ElementosGlobales)
            {
                if (elementoGlobal.State.IsEmpty) continue;
                string json = Encoding.UTF8.GetString(elementoGlobal.State.ToByteArray());
                _estado[elementoGlobal.Name] = JObject.Parse(json);
            }
        }
    }
}