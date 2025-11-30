using UnityEngine;

[RequireComponent(typeof(Camera))]
public class SeguirMovimientoGameObject : MonoBehaviour
{
    private Camera cam;
    private Transform target;

    [Header("Dead Zone")]
    public float deadZoneRadius = 100f; // Radio en píxeles del círculo central

    [Header("Smooth Follow")]
    public float smoothTime = 0.25f;
    private Vector3 velocity = Vector3.zero;

    public Vector3 offset = new(0, 0, -10);

    void Awake()
    {
        cam = GetComponent<Camera>();
    }

    void LateUpdate()
    {
        if (target == null) return;

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
    }    

    public void SeguirConCamara(GameObject newTarget)
    {
        if (newTarget == null)
        {
            target = null;
            return;
        }
        target = newTarget.transform;
    }

    public void DejarDeSeguirConCamara()
    {
        SeguirConCamara(null);
    }
}
