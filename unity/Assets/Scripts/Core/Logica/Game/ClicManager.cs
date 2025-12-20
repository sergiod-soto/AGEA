using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;



public class ClicManager : MonoBehaviour
{

    IBotsLogica botsLogica;
    IControlHUDLogica controlHUDLogica;

    private void Awake()
    {
        botsLogica = ServiceLocator.Instance.Get<IBotsLogica>();
        controlHUDLogica = ServiceLocator.Instance.Get<IControlHUDLogica>();
    }

    void Update()
    {
        if (Mouse.current.leftButton.wasPressedThisFrame)
        {
            if (EventSystem.current.IsPointerOverGameObject())
                // se ha hecho clic en UI
                return;

            Vector2 mousePos = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue());
            RaycastHit2D hit = Physics2D.Raycast(mousePos, Vector2.zero);

            if (hit.collider != null)
            {
                // se ha hecho clic en algo con hitbox

                // si se hace clic en un bot
                if (hit.collider.TryGetComponent<BotInfo>(out var bot_inf))
                {
                    botsLogica.ClicEnBot(bot_inf.gameObject);
                    return;
                }
            }
            else
            {
                controlHUDLogica.CloseBotHUD();
            }
        }
    }
}
