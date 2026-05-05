import type { Metadata } from "next";
import Link from "next/link";

const contactEmail = "aqina_marketing@aqinafarm.com";
const whatsappNumber = "+65 9626 5734";
const whatsappHref = "https://wa.me/6596265734";

type PolicySection = {
  id: string;
  title: string;
  zhTitle: string;
  body: string[];
  zhBody: string[];
};

const policySections: PolicySection[] = [
  {
    id: "who-we-are",
    title: "Who we are",
    zhTitle: "我们是谁",
    body: [
      "This Privacy Policy explains how Aqina Singapore and Aqina Farm Singapore collect, use, disclose, retain, and protect personal data when you visit our website, contact us, place an order, or interact with our Facebook Page, Messenger, WhatsApp, advertisements, customer service, and related digital services.",
      "We handle personal data in line with Singapore's Personal Data Protection Act 2012 (PDPA) and other applicable requirements.",
    ],
    zhBody: [
      "本隐私政策说明 Aqina Singapore 与 Aqina Farm Singapore 在您浏览网站、联系我们、下单，或通过 Facebook Page、Messenger、WhatsApp、广告、客服及相关数码服务互动时，如何收集、使用、披露、保留和保护个人资料。",
      "我们会根据新加坡《个人资料保护法令 2012》（PDPA）及适用要求处理个人资料。",
    ],
  },
  {
    id: "personal-data",
    title: "Personal data we collect",
    zhTitle: "我们收集的个人资料",
    body: [
      "Depending on your interaction with us, we may collect your name, phone number, email address, delivery address, order details, payment reference or payment screenshot, enquiry content, product interests, health or gifting preferences that you choose to share, and customer service notes.",
      "When you contact us through Facebook, Messenger, or WhatsApp, we may receive your profile name, platform user ID, message content, comment content, attachments you send, timestamps, delivery status, and conversation history needed to respond to your enquiry.",
      "We may also collect website and device information such as pages viewed, approximate location derived from network data, browser type, referring links, and cookie or analytics identifiers.",
    ],
    zhBody: [
      "根据您与我们的互动方式，我们可能收集您的姓名、电话号码、电邮、送货地址、订单资料、付款参考或付款截图、询问内容、产品兴趣、您主动分享的调养或送礼偏好，以及客服记录。",
      "当您通过 Facebook、Messenger 或 WhatsApp 联系我们时，我们可能接收您的平台显示名称、平台用户 ID、讯息内容、留言内容、您发送的附件、时间戳、发送状态，以及为回复您而需要的对话记录。",
      "我们也可能收集网站和设备资料，例如浏览页面、由网络资料推断的大致位置、浏览器类型、来源链接，以及 cookie 或分析识别码。",
    ],
  },
  {
    id: "meta-whatsapp-data",
    title: "How we use Facebook, Messenger, and WhatsApp data",
    zhTitle: "我们如何使用 Facebook、Messenger 与 WhatsApp 资料",
    body: [
      "If you leave a buying-intent comment on an Aqina-owned Facebook Page, our system may send one public reply and one Messenger private reply so we can continue the product enquiry in a private conversation.",
      "If you reply to our Messenger or WhatsApp messages, your message may be processed in our admin CRM and AI sales assistant flow for customer support, product consultation, order assistance, delivery follow-up, and service quality monitoring.",
      "We do not sell personal data. We do not use Facebook, Messenger, or WhatsApp data to build unrelated profiles or to contact you about unrelated third-party products.",
    ],
    zhBody: [
      "如果您在 Aqina 自有 Facebook Page 留下带有购买意图的评论，系统可能发送一次公开回复和一次 Messenger 私讯，以便我们在私人对话中继续处理产品咨询。",
      "如果您回复我们的 Messenger 或 WhatsApp 讯息，您的讯息可能进入我们的 admin CRM 和 AI sales assistant 流程，用于客服、产品咨询、订单协助、配送跟进和服务质量管理。",
      "我们不会出售个人资料。我们不会使用 Facebook、Messenger 或 WhatsApp 资料建立无关画像，也不会用这些资料向您推广无关的第三方产品。",
    ],
  },
  {
    id: "ai-crm",
    title: "AI sales assistant and CRM processing",
    zhTitle: "AI 销售助理与 CRM 处理",
    body: [
      "We may use automated tools and AI-assisted systems to understand enquiries, suggest product information, prepare replies, classify customer needs, and support follow-up. Human administrators may review conversations and take over where needed.",
      "AI-assisted replies are used to support customer service and sales consultation. They do not replace your right to contact our team directly for clarification, correction, or assistance.",
    ],
    zhBody: [
      "我们可能使用自动化工具和 AI 辅助系统来理解咨询、建议产品资料、准备回复、分类顾客需求并支持后续跟进。必要时，管理员会查看对话并接手处理。",
      "AI 辅助回复用于支持客服与销售咨询，不影响您直接联系我们团队要求说明、更正或协助的权利。",
    ],
  },
  {
    id: "purposes",
    title: "Purposes for using personal data",
    zhTitle: "使用个人资料的目的",
    body: [
      "We may use personal data to respond to enquiries, process orders, verify payment, arrange delivery, provide customer support, manage customer relationships, send service updates, improve our website and service experience, prevent misuse, comply with legal obligations, and protect our rights.",
      "Where permitted by law or with your consent, we may send product information, offers, reminders, and follow-up messages about Aqina products and services.",
    ],
    zhBody: [
      "我们可能使用个人资料来回复咨询、处理订单、核对付款、安排配送、提供客服、管理顾客关系、发送服务更新、改善网站和服务体验、防止滥用、遵守法律义务，以及保护我们的权利。",
      "在法律允许或取得您同意的情况下，我们可能发送 Aqina 产品与服务相关的资料、优惠、提醒和跟进讯息。",
    ],
  },
  {
    id: "marketing-opt-out",
    title: "Marketing, follow-up, and opt-out",
    zhTitle: "营销、跟进与退出",
    body: [
      "You may opt out of marketing or automated follow-up at any time by replying STOP, Stop, 停止, 不要再发, or a similar opt-out message in Messenger or WhatsApp.",
      `You may also email ${contactEmail} to request that we stop using your personal data for marketing or follow-up purposes.`,
      "Operational messages, such as order, delivery, payment, service, or safety-related messages, may still be sent where necessary to complete your request or comply with legal obligations.",
    ],
    zhBody: [
      "您可随时在 Messenger 或 WhatsApp 回复 STOP、Stop、停止、不要再发，或类似退出讯息，以停止营销或自动跟进。",
      `您也可以电邮 ${contactEmail}，要求我们停止将您的个人资料用于营销或跟进用途。`,
      "为了完成您的请求或遵守法律义务，我们仍可能在必要时发送订单、配送、付款、服务或安全相关的操作性讯息。",
    ],
  },
  {
    id: "disclosure",
    title: "Disclosure to service providers",
    zhTitle: "向服务供应商披露",
    body: [
      "We may disclose personal data to service providers who help us operate our website, payment verification, delivery, CRM, analytics, cloud hosting, messaging, automation, customer service, accounting, security, and compliance processes.",
      "These providers are only given access to personal data needed to perform their services for us, and they are expected to protect personal data in line with applicable requirements.",
    ],
    zhBody: [
      "我们可能向协助我们运营网站、付款核对、配送、CRM、分析、云端托管、讯息发送、自动化、客服、会计、安全和合规流程的服务供应商披露个人资料。",
      "这些供应商只会取得为我们提供服务所需的个人资料，并应根据适用要求保护个人资料。",
    ],
  },
  {
    id: "retention",
    title: "Data retention",
    zhTitle: "资料保留",
    body: [
      "We retain personal data for as long as needed to fulfil the purposes for which it was collected, to provide services, to resolve disputes, to comply with legal or accounting requirements, and to protect legitimate business interests.",
      "When personal data is no longer needed for legal or business purposes, we will take reasonable steps to delete, anonymise, or otherwise stop associating it with you.",
    ],
    zhBody: [
      "我们会在达成收集目的、提供服务、解决争议、遵守法律或会计要求，以及保护正当商业利益所需的期间内保留个人资料。",
      "当个人资料不再因法律或商业目的而需要时，我们会采取合理步骤删除、匿名化，或以其他方式停止将资料与您关联。",
    ],
  },
  {
    id: "data-deletion",
    title: "Access, correction, and deletion requests",
    zhTitle: "查阅、更正与删除资料请求",
    body: [
      `You may request access to, correction of, or deletion of personal data that we hold about you by emailing ${contactEmail}.`,
      "Please include enough information for us to identify your record, such as your name, phone number, email address, Facebook or WhatsApp contact details, and the nature of your request.",
      "We may need to verify your identity before acting on a request. If we cannot delete certain records because of legal, accounting, security, or dispute-resolution obligations, we will explain the reason where appropriate.",
    ],
    zhBody: [
      `您可以电邮 ${contactEmail}，要求查阅、更正或删除我们持有的关于您的个人资料。`,
      "请提供足够资料让我们识别您的记录，例如姓名、电话号码、电邮、Facebook 或 WhatsApp 联系资料，以及您的请求内容。",
      "我们可能需要先核实您的身份再处理请求。如果因法律、会计、安全或争议处理义务而无法删除部分记录，我们会在适当情况下说明原因。",
    ],
  },
  {
    id: "cookies",
    title: "Cookies and analytics",
    zhTitle: "Cookie 与分析",
    body: [
      "Our website may use cookies, pixels, analytics tags, and similar technologies to keep the site working, understand page performance, improve user experience, measure advertising effectiveness, and protect against misuse.",
      "You can manage cookies through your browser settings. Disabling cookies may affect some website functions.",
    ],
    zhBody: [
      "我们的网站可能使用 cookie、像素、分析标签和类似技术，以维持网站运作、了解页面表现、改善用户体验、衡量广告效果，并防止滥用。",
      "您可以通过浏览器设置管理 cookie。停用 cookie 可能影响部分网站功能。",
    ],
  },
  {
    id: "security",
    title: "Security",
    zhTitle: "资料安全",
    body: [
      "We use reasonable administrative, technical, and organisational measures to protect personal data from unauthorised access, collection, use, disclosure, copying, modification, disposal, or similar risks.",
      "No internet transmission or electronic storage method is completely secure, but we regularly review our safeguards and limit access to personal data to those who need it for business purposes.",
    ],
    zhBody: [
      "我们采用合理的行政、技术和组织措施，保护个人资料免受未经授权的访问、收集、使用、披露、复制、修改、处置或类似风险。",
      "互联网传输或电子储存方式无法保证完全安全，但我们会定期检视保护措施，并将个人资料访问权限限制在有业务需要的人员范围内。",
    ],
  },
  {
    id: "transfers",
    title: "International transfers",
    zhTitle: "跨境传输",
    body: [
      "Some service providers, cloud systems, or messaging platforms may process data outside Singapore. Where personal data is transferred overseas, we take reasonable steps to ensure it receives a standard of protection comparable to that required under Singapore law.",
    ],
    zhBody: [
      "部分服务供应商、云端系统或讯息平台可能在新加坡以外处理资料。如个人资料被传输至海外，我们会采取合理步骤，确保其获得与新加坡法律要求相当的保护标准。",
    ],
  },
  {
    id: "changes",
    title: "Changes to this policy",
    zhTitle: "政策更新",
    body: [
      "We may update this Privacy Policy from time to time. The latest version will be published on this page with the effective date and last updated date.",
    ],
    zhBody: [
      "我们可能不时更新本隐私政策。最新版本会发布在本页面，并列明生效日期和最后更新日期。",
    ],
  },
];

export const metadata: Metadata = {
  title: "Privacy Policy | Aqina Singapore",
  description:
    "Aqina Singapore privacy policy for website, Facebook Messenger, WhatsApp, AI sales assistant, CRM, marketing opt-out, and data deletion requests.",
  alternates: {
    canonical: "/privacy-policy",
  },
};

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen overflow-x-hidden bg-[#f8f4e9] text-[#10251d]">
      <section className="border-b border-[#dccfb5] bg-[#10251d] text-[#fff9ea]">
        <div className="mx-auto flex w-full max-w-5xl min-w-0 flex-col gap-8 px-5 py-10 md:px-8 md:py-14">
          <Link
            id="privacy-policy-home-link"
            href="/"
            className="w-fit text-sm font-semibold text-[#d4af37] hover:text-[#ffe18b]"
          >
            Aqina Singapore
          </Link>
          <div className="max-w-3xl min-w-0">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#d4af37]">
              Privacy Policy
            </p>
            <h1
              id="privacy-policy-title"
              className="mt-4 break-words text-3xl font-bold leading-tight [overflow-wrap:anywhere] sm:text-4xl md:text-5xl"
            >
              Privacy Policy / 隐私政策
            </h1>
            <p className="mt-5 break-words text-base leading-8 text-[#e9dfc7] [overflow-wrap:anywhere] md:text-lg">
              This page explains how Aqina Singapore handles personal data across our website,
              Facebook Page, Messenger, WhatsApp, AI-assisted sales flow, and admin CRM.
            </p>
            <p className="mt-3 break-words text-base leading-8 text-[#e9dfc7] [overflow-wrap:anywhere] md:text-lg">
              本页面说明 Aqina Singapore 如何在网站、Facebook Page、Messenger、WhatsApp、
              AI 辅助销售流程和后台 CRM 中处理个人资料。
            </p>
          </div>
          <div className="grid gap-3 text-sm text-[#f4ead1] sm:grid-cols-2">
            <div>
              <p className="font-semibold text-[#d4af37]">Effective date / 生效日期</p>
              <p>5 May 2026</p>
            </div>
            <div>
              <p className="font-semibold text-[#d4af37]">Last updated / 最后更新</p>
              <p>5 May 2026</p>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-[#e7dcc5] bg-[#fffaf0]">
        <div className="mx-auto grid w-full max-w-5xl min-w-0 gap-6 px-5 py-8 md:grid-cols-[0.85fr_1.15fr] md:px-8">
          <nav
            id="privacy-policy-navigation"
            aria-label="Privacy policy sections"
            className="grid min-w-0 gap-2 text-sm"
          >
            {policySections.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className="min-w-0 break-words rounded-md border border-[#eadfc7] bg-white px-3 py-2 font-semibold text-[#2d4439] [overflow-wrap:anywhere] hover:border-[#d4af37] hover:text-[#10251d]"
              >
                {section.title}
              </a>
            ))}
          </nav>
          <div className="min-w-0 rounded-md border border-[#eadfc7] bg-white p-5">
            <h2 className="text-xl font-bold">Data deletion / 删除资料</h2>
            <p className="mt-3 break-words leading-7 text-[#4d6158] [overflow-wrap:anywhere]">
              For Meta data deletion requests, use this page URL with the anchor:
            </p>
            <a
              id="privacy-policy-data-deletion-url"
              href="#data-deletion"
              className="mt-2 block max-w-full break-all font-semibold text-[#8c6a13] hover:text-[#10251d]"
            >
              https://aqina-sg.web.app/privacy-policy#data-deletion
            </a>
            <p className="mt-4 break-words leading-7 text-[#4d6158] [overflow-wrap:anywhere]">
              Contact / 联系：{" "}
              <a
                id="privacy-policy-email"
                href={`mailto:${contactEmail}`}
                className="break-all font-semibold text-[#8c6a13] hover:text-[#10251d]"
              >
                {contactEmail}
              </a>
            </p>
          </div>
        </div>
      </section>

      <article className="mx-auto w-full max-w-5xl min-w-0 px-5 py-10 md:px-8 md:py-14">
        <div className="min-w-0 space-y-8">
          {policySections.map((section, index) => (
            <section
              key={section.id}
              id={section.id}
              className="min-w-0 scroll-mt-6 border-b border-[#dfd2ba] pb-8 last:border-b-0"
            >
              <p className="text-sm font-semibold text-[#8c6a13]">
                {String(index + 1).padStart(2, "0")}
              </p>
              <h2 className="mt-2 break-words text-2xl font-bold leading-snug [overflow-wrap:anywhere] md:text-3xl">
                {section.title}
              </h2>
              <h3 className="mt-1 break-words text-xl font-bold leading-snug text-[#53695f] [overflow-wrap:anywhere]">
                {section.zhTitle}
              </h3>
              <div className="mt-5 grid min-w-0 gap-6 md:grid-cols-2">
                <div className="min-w-0 space-y-4">
                  {section.body.map((paragraph) => (
                    <p
                      key={paragraph}
                      className="break-words leading-8 text-[#31473d] [overflow-wrap:anywhere]"
                    >
                      {paragraph}
                    </p>
                  ))}
                </div>
                <div className="min-w-0 space-y-4 border-l-0 border-[#eadfc7] md:border-l md:pl-6">
                  {section.zhBody.map((paragraph) => (
                    <p
                      key={paragraph}
                      className="break-words leading-8 text-[#31473d] [overflow-wrap:anywhere]"
                    >
                      {paragraph}
                    </p>
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>
      </article>

      <section className="border-t border-[#dccfb5] bg-[#10251d] text-[#fff9ea]">
        <div className="mx-auto flex w-full max-w-5xl min-w-0 flex-col gap-5 px-5 py-8 md:flex-row md:items-center md:justify-between md:px-8">
          <div className="min-w-0">
            <h2 className="break-words text-xl font-bold [overflow-wrap:anywhere]">
              Contact Aqina Singapore
            </h2>
            <p className="mt-2 break-words text-sm leading-6 text-[#e9dfc7] [overflow-wrap:anywhere]">
              For privacy, access, correction, deletion, or opt-out requests, contact us by email
              or WhatsApp.
            </p>
            <p className="mt-1 break-words text-sm leading-6 text-[#e9dfc7] [overflow-wrap:anywhere]">
              如需隐私、查阅、更正、删除或退出营销，请通过电邮或 WhatsApp 联系我们。
            </p>
          </div>
          <div className="flex min-w-0 flex-col gap-3 sm:flex-row">
            <a
              id="privacy-policy-contact-email"
              href={`mailto:${contactEmail}`}
              className="max-w-full break-words rounded-md bg-[#d4af37] px-4 py-3 text-center text-sm font-bold text-[#10251d] [overflow-wrap:anywhere] hover:bg-[#f1cf63]"
            >
              Email privacy request
            </a>
            <a
              id="privacy-policy-contact-whatsapp"
              href={whatsappHref}
              className="max-w-full break-words rounded-md border border-[#d4af37] px-4 py-3 text-center text-sm font-bold text-[#fff9ea] [overflow-wrap:anywhere] hover:bg-[#213e33]"
            >
              WhatsApp {whatsappNumber}
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
