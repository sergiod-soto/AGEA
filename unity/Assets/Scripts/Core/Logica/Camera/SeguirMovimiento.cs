using Newtonsoft.Json.Linq;
using System;
using UnityEngine;

[RequireComponent(typeof(Camera))]
public class SeguirMovimientoGameObject : MonoBehaviour
{

    Camera cam;
    Transform target;
    GameObject bot;

    public float deadZoneRadius = 100f; // Radio en píxeles del círculo central
    public float smoothTime = 0.25f;
    private Vector3 velocity = Vector3.zero;

    public Vector3 offset = new(0, 0, -10);

    float timer = 0f;

    void Awake()
    {
        
    }

    void Start()
    {
        cam = GetComponent<Camera>();
        bot = null;
    }

    void LateUpdate()
    {
        if (target == null) return;

        timer += Time.deltaTime;



        // Convertimos la posición del target a pantalla
        Vector3 targetScreenPos = cam.WorldToScreenPoint(target.position);

        // Centro de la pantalla
        Vector2 screenCenter = new(Screen.width / 2f, Screen.height / 2f);

        // Distancia entre el target y el centro
        float dist = Vector2.Distance(targetScreenPos, screenCenter);

        // Si está dentro del círculo, no movemos la cámara
        if (dist < deadZoneRadius) return;

        // Si está fuera, movemos la cámara suavemente hacia el objetivo
        Vector3 desiredPosition = target.position + offset;

        transform.position = Vector3.SmoothDamp(
            transform.position,
            desiredPosition,
            ref velocity,
            smoothTime
        );

        if (timer < 0.1f) return;
        timer = 0f;

        if (bot != null)
        {
            Debug.Log("hay que pensar que deberia ir aqui, ahora no quiero hacerlo");
        }

    }

    public void SeguirConCamara(GameObject newTarget)
    {
        bot = null;
        if (newTarget == null)
        {
            target = null;
            bot = null;
            return;
        }
        SetBot_A_Actualizar(newTarget);
        target = newTarget.transform;
    }

    public void DejarDeSeguirConCamara()
    {
        SeguirConCamara(null);
    }

    /* 
     *  Me aseguro que el lo que se pasa sea un bot
     */
    public void SetBot_A_Actualizar(GameObject objeto)
    {
        throw new NotImplementedException("SetBot_A_Actualizar");
        //if (objeto.TryGetComponent<BotInfo>(out _))
        //{
        //    bot = objeto;
        //}
    }
}
