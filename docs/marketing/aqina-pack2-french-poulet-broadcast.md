# Aqina Pack 2 French Poulet Broadcast

Date: 2026-06-06

## WhatsApp Broadcast

Use two WhatsApp marketing templates so campaign delivery can match the customer's detected chatbot language.

Chinese template:

- `name`: `aqina_pack2_french_poulet_offer_zh`
- `language_code`: `zh_CN`
- `category`: `MARKETING`
- `customer_locale`: `zh`
- `body`: `Aqina 纯鸡精现在有 2盒优惠：2盒 SGD79.80，等于每盒 SGD39.90，并送 1包 French Poulet Cut Part 五选一（market value SGD8）。回复“2盒”我帮您确认赠品选择。`
- `footer`: `回复 STOP 可停止收到促销通知`
- `buttons`: `我要2盒`, `选择赠品`

English template:

- `name`: `aqina_pack2_french_poulet_offer_en`
- `language_code`: `en_US`
- `category`: `MARKETING`
- `customer_locale`: `en`
- `body`: `AQINA Pure Chicken Essence offer: 2 boxes for SGD79.80 (SGD39.90/box) with 1 French Poulet Cut Part gift choice, market value SGD8. Reply “2 boxes” to choose your gift.`
- `footer`: `Reply STOP to opt out of promotion updates`
- `buttons`: `I want 2 boxes`, `Gift choices`

Admin flow:

1. Open Admin Inbox > Templates.
2. Click `中文 Promotion` and `English Promotion` to submit both templates to Meta review.
3. Wait for Meta approval, then click `Sync from Meta`.
4. Open Campaigns and create two drafts:
   - Chinese: template `aqina_pack2_french_poulet_offer_zh`, language `zh_CN`, audience `Chinese / unknown`.
   - English: template `aqina_pack2_french_poulet_offer_en`, language `en_US`, audience `English`.
5. Preview each campaign and confirm the eligible count before launch.
6. Launch only after confirming the WABA, phone number, recipient count, and promotion inventory.

The current app only submits text + footer + quick-reply templates. To include the promotion image inside the WhatsApp template itself, add a Meta template media-header upload flow or create the media-header template manually in WhatsApp Manager. The image is already sent automatically when a customer enters the chatbot conversation.

## Messenger Promotion Update

Messenger does not use WhatsApp-style template submission for broadcast. Do not send promotional free-form Messenger updates to every past customer outside the allowed messaging window.

Recommended paths:

1. Send the promotion image and text only to Messenger contacts whose 24-hour customer window is open.
2. Use Click-to-Messenger or Sponsored Messages in Meta Ads Manager to reach/re-engage Messenger users at scale.
3. Add a Messenger recurring notification opt-in flow for future promotions, then send future updates only to subscribers.
4. Publish the promotion on Facebook/Instagram feed or story and use comment-to-Messenger automation to restart compliant conversations.

Launch gate:

- Confirm Meta Page, WABA, WhatsApp phone number, ad account, and sending audience.
- Confirm French Poulet gift inventory before broadcast.
- Confirm opt-out handling remains active: customers can reply `STOP` / `退订`.
