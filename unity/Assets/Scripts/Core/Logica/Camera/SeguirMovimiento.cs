using UnityEngine;

[RequireComponent(typeof(Camera))]
public class SeguirMovimientoGameObject : MonoBehaviour
{
    private Camera cam;              // la cámara en la que está este script
    private Transform target;        // objetivo actual

    public float smoothTime = 0.25f; // suavidad del movimiento
    private Vector3 velocity = Vector3.zero;

    public Vector3 offset;

    void Awake()
    {
        // obtenemos la cámara en la que está este script
        cam = GetComponent<Camera>();
    }

    void LateUpdate()
    {
        if (target == null) return;

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
