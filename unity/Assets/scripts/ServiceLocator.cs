using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

[DefaultExecutionOrder(-100)]  // intenta ejecutarse antes que otros scripts
public class ServiceLocator : MonoBehaviour
{
    public static ServiceLocator Instance { get; private set; }

    // Diccionario: interfaz -> instancia
    private readonly Dictionary<Type, object> services = new();

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject); // opcional según tu caso

        RegisterAllServicesInScene();

        // Registrar servicios también cuando cambias de escena
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }

    private void OnSceneLoaded(Scene s, LoadSceneMode mode)
    {
        RegisterAllServicesInScene();
    }

    private void RegisterAllServicesInScene()
    {
        services.Clear();

        // Encuentra TODOS los MonoBehaviour (activos e inactivos)
        var allMono = FindObjectsByType<MonoBehaviour>(
            FindObjectsInactive.Include,
            FindObjectsSortMode.None
        );

        foreach (var mb in allMono)
        {
            var mbType = mb.GetType();

            // Solo registramos scripts que implementen IService
            if (mb is not IService)
                continue;

            // Obtener todas las interfaces de este script que derivan de IService
            var interfaces = mbType.GetInterfaces()
                .Where(i => typeof(IService).IsAssignableFrom(i) && i != typeof(IService));

            foreach (var iface in interfaces)
            {
                if (services.ContainsKey(iface))
                {
                    Debug.LogWarning(
                        $"ServiceLocator: ya existe un servicio registrado para {iface.Name}. " +
                        $"Se ignora la implementación {mbType.Name}."
                    );
                    continue;
                }

                services[iface] = mb;
                // Debug.Log($"ServiceLocator: Registrado servicio {mbType.Name} como {iface.Name}");
            }
        }
    }

    // Obtener un servicio (lanza excepción si no existe)
    public T Get<T>() where T : class
    {
        if (services.TryGetValue(typeof(T), out var s))
            return s as T;

        throw new Exception(
            $"ServiceLocator: No se encontró el servicio solicitado: {typeof(T).Name}"
        );
    }

    // Obtener un servicio sin lanzar excepción
    public bool TryGet<T>(out T service) where T : class
    {
        if (services.TryGetValue(typeof(T), out var s))
        {
            service = s as T;
            return true;
        }

        service = null;
        return false;
    }
}