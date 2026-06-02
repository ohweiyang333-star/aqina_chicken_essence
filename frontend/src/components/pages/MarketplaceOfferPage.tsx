'use client';

import { useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import Image from 'next/image';
import { 
  Check, 
  MessageCircle, 
  ShieldCheck, 
  Star, 
  Truck, 
  HelpCircle, 
  Award, 
  Flame, 
  RotateCcw,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import CheckoutModal from '@/components/CheckoutModal';
import useLandingProducts from '@/hooks/useLandingProducts';
import { getWhatsAppHref } from '@/lib/site-config';

// 新加坡本地 Verified Reviews
const VERIFIED_REVIEWS = [
  {
    name: '敏仪 (Min Yi)',
    role: '金融行业项目经理 | 职场保养',
    rating: 5,
    date: '2天前',
    content: '之前喝瓶装鸡精总是觉得有一股腥味，要一口气灌下去。Aqina 这个纯鸡精入口真的很像熬得很浓的清鸡汤，非常鲜甜而且完全不油。最近项目上线连续加班，我每天午后温热一包，喝完感觉人没那么发虚，晚间开会脑子也挺清楚。真心推荐！',
    image: '/ugc/office-corner.jpg',
    avatar: '/ugc/sg-young-chinese-woman-campus.webp',
  },
  {
    name: '林太太 (Mrs. Lim)',
    role: '全职妈妈 | 产后与家庭调理',
    rating: 5,
    date: '5天前',
    content: '给生完二胎的妹妹买的。她坐月子胃口不好，这个鸡精免去了自己炖鸡汤的油腻和繁琐。2盒送的法式鸡肉碎非常新鲜，刚好用来做月子餐。妹妹说喝了几天奶水很足，精神恢复得也快。我自己也顺便订了1盒，确实无添加，全家喝着都安心。',
    image: '/ugc/morning-kitchen.jpg',
    avatar: '/ugc/sg-middle-aged-malay-woman.webp',
  },
  {
    name: '陈先生 (Mr. Tan)',
    role: '销售主管 | 银发日常保健',
    rating: 4.9,
    date: '1周前',
    content: '买给爸妈补身体的。爸妈年纪大了肠胃弱，很多补品吃了吸收不好。Aqina 的黄梨酵素喂养鸡精分子小，爸妈反馈喝了胃里暖暖的，很舒服，食欲也变好了。新加坡现货发货非常快，2天就收到货了，免运费很省心！',
    image: '/ugc/cozy-sofa.jpg',
    avatar: '/ugc/sg-middle-aged-chinese-man.webp',
  }
];

const FAQ_ITEMS = [
  {
    q: '为什么说 Aqina 纯鸡精“零负担”？它和普通瓶装鸡精有什么区别？',
    a: '普通瓶装鸡精往往来源复杂且有添加剂与腥味。Aqina 纯鸡精源自单一农场、吃 MD2 黄梨酵素长大的健康鸡。通过 7 天双重慢炼滴存，去油去腥，100% 纯鸡精且不加一滴水。入口清澈如清汤，肠胃不需要额外工作就能直接转化为元气，特别适合虚弱期、孕产妇和高压上班族。'
  },
  {
    q: '2盒送的 French Poulet 赠品怎么发货？如何选择？',
    a: '当您下单 2 盒免运配套时，可以在下方直接选择法式鸡肉赠品（五选一）。这批赠品全部由我们的新加坡冷链配送团队与纯鸡精一同为您送达，确保新鲜度。您也可以在付款前通过 WhatsApp 与我们的中文客服确认赠品意向。'
  },
  {
    q: '如何进行 PayNow 付款并提交订单？',
    a: '选择好您心仪的配套后，点击“PayNow 直接下单”。在弹出的结账框内扫描我们的官方 PayNow QR 二维码进行转账，付款备注填写您的 WhatsApp 电话。转账成功后截图并在此上传收据即可完成下单。我们的客服会在 1-3 小时内人工核对并给您发送 WhatsApp 确认短信。'
  }
];

export default function MarketplaceOfferPage() {
  const t = useTranslations('Index');
  const locale = useLocale();
  
  const {
    products,
    isLoading,
    selectedProduct,
    isCheckoutOpen,
    handleBuyNow,
    closeCheckout,
  } = useLandingProducts();

  // 默认选中 Variant 2 (pack2)，因为 2 盒最划算且送赠品
  const [activeTab, setActiveTab] = useState<'pack1' | 'pack2'>('pack2');
  const [selectedGift, setSelectedGift] = useState('French Poulet Minced 400g');

  const activeProduct = products.find(p => p.id === activeTab) || products[0];

  const giftOptions = [
    { value: 'French Poulet Minced 400g', label: '法式鸡肉碎 400g (市场价值 $8)' },
    { value: 'French Poulet 3 Joint Wing 500g', label: '法式三节翅 500g (市场价值 $8)' },
    { value: 'French Poulet Boneless Breast 350g', label: '法式去骨鸡胸肉 350g (市场价值 $8)' },
    { value: 'French Poulet Whole Leg 400g', label: '法式整只鸡腿 400g (市场价值 $8)' },
    { value: 'French Poulet Half Chicken Cut 4 Pieces 500g', label: '法式半只切块鸡 500g (市场价值 $8)' },
  ];

  const handleWhatsAppOrder = () => {
    const giftInfo = activeTab === 'pack2' ? `，赠品选择：${selectedGift}` : '';
    const message = `Hi Aqina SG，我想通过 WhatsApp 预订新优惠套餐：【${activeTab === 'pack1' ? '1盒 7天试喝装' : '2盒 14天免运常备装'}】${giftInfo}。请帮我确认订单！`;
    const whatsappUrl = getWhatsAppHref(message);
    window.open(whatsappUrl, '_blank');
  };

  const handlePayNowSubmit = () => {
    // 动态把选中的赠品加到选中的产品属性上，CheckoutModal 会自动读取它
    if (activeProduct) {
      const checkoutProduct = {
        ...activeProduct,
        // 把选中的赠品直接拼在 label 或者是 product.name 后面，以透传给 modal 内部
        label: activeTab === 'pack2' 
          ? `${activeProduct.label} (已选赠: ${giftOptions.find(g => g.value === selectedGift)?.label || selectedGift})`
          : activeProduct.label
      };
      handleBuyNow(checkoutProduct);
    }
  };

  return (
    <div className="min-h-screen bg-[#faf8f5] text-charcoal font-sans selection:bg-primary/20">
      {/* 顶部顶级活动跑马灯 */}
      <div className="w-full bg-[#1b261b] text-[#f2e7d5] py-2.5 px-4 overflow-hidden border-b border-primary/20 relative z-20">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-6 text-xs font-bold tracking-wider uppercase md:px-6">
          <div className="flex items-center gap-2">
            <Flame size={14} className="text-primary animate-pulse shrink-0" />
            <span>【新加坡现货】全场配套直接免邮费！</span>
          </div>
          <div className="hidden sm:flex items-center gap-3">
            <span className="opacity-60">MD2黄梨酵素喂养</span>
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            <span className="opacity-60">JAKIM Halal 认证</span>
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            <span className="opacity-60">2-3天冷链配送</span>
          </div>
        </div>
      </div>

      {/* 极简尊贵主 Buy Box 排版区 */}
      <main className="max-w-7xl mx-auto px-4 py-8 md:py-12 md:px-8 grid gap-8 lg:grid-cols-12 items-start">
        
        {/* 左侧：奢华产品主图与 Gallery */}
        <section className="lg:col-span-7 space-y-6">
          <div className="relative aspect-[4/3] rounded-3xl overflow-hidden border border-charcoal/5 shadow-xl bg-white">
            <Image
              src="/ugc/morning-kitchen.jpg"
              alt="Aqina Pure Chicken Essence Serving Scene"
              fill
              priority
              className="object-cover"
            />
            {/* 左上角高端爆款角标 */}
            <div className="absolute top-5 left-5 bg-gradient-to-r from-primary to-primary-light text-charcoal-dark font-black px-4 py-2 rounded-xl text-xs shadow-md tracking-wider flex items-center gap-1.5">
              <Sparkles size={13} />
              <span>新加坡热销首选</span>
            </div>
          </div>

          {/* 小图平铺 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-charcoal/5 shadow-sm bg-white cursor-pointer hover:border-primary transition-all">
              <Image src="/ugc/sg-young-fitness-woman.webp" alt="Aqina product box" fill className="object-cover" />
            </div>
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-charcoal/5 shadow-sm bg-white cursor-pointer hover:border-primary transition-all">
              <Image src="/ugc/sg-middle-aged-chinese-man.webp" alt="Aqina serving" fill className="object-cover" />
            </div>
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-charcoal/5 shadow-sm bg-white cursor-pointer hover:border-primary transition-all">
              <Image src="/ugc/sg-young-indian-home-woman.webp" alt="Aqina gift fresh chicken" fill className="object-cover" />
            </div>
          </div>

          {/* 顶奢三项正品承诺 */}
          <div className="grid grid-cols-3 gap-3 bg-white p-5 rounded-2xl border border-charcoal/5 shadow-sm text-center">
            <div className="space-y-1">
              <ShieldCheck className="mx-auto text-primary" size={24} />
              <p className="text-[11px] font-bold text-charcoal/40 uppercase tracking-wider">配方承诺</p>
              <p className="text-xs font-black">100%纯无添加水</p>
            </div>
            <div className="space-y-1 border-x border-charcoal/10">
              <Truck className="mx-auto text-primary" size={24} />
              <p className="text-[11px] font-bold text-charcoal/40 uppercase tracking-wider">配送承诺</p>
              <p className="text-xs font-black">全岛冷链免运费</p>
            </div>
            <div className="space-y-1">
              <Award className="mx-auto text-primary" size={24} />
              <p className="text-[11px] font-bold text-charcoal/40 uppercase tracking-wider">健康承诺</p>
              <p className="text-xs font-black">JAKIM Halal认证</p>
            </div>
          </div>
        </section>

        {/* 右侧：Buy Box 控制中心 */}
        <section className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl p-6 md:p-8 border border-charcoal/5 shadow-xl space-y-6 relative overflow-hidden">
            {/* 炫彩光晕装饰 */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

            {/* 产品核心基本信息 */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-primary text-sm font-bold tracking-wider">
                <div className="flex text-amber-400">
                  <Star size={14} fill="currentColor" />
                  <Star size={14} fill="currentColor" />
                  <Star size={14} fill="currentColor" />
                  <Star size={14} fill="currentColor" />
                  <Star size={14} fill="currentColor" />
                </div>
                <span className="font-extrabold">4.93★</span>
                <span className="text-charcoal/40 text-xs">| 新加坡地区已售 2.4k+ 盒</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight text-charcoal">
                Aqina 黄梨酵素纯鸡精 <span className="text-base font-normal text-charcoal/60 block mt-1">(7包 x 60g / 盒)</span>
              </h1>
            </div>

            {/* 黄金大促价格展示 */}
            <div className="bg-[#fcfaf5] p-5 rounded-2xl border border-primary/20 space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-bold text-charcoal/55">当前优惠价</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-xs font-bold text-primary">SGD</span>
                  <span className="text-3xl font-black text-primary">
                    {activeTab === 'pack1' ? '47.90' : '79.80'}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-charcoal/5 text-xs text-charcoal/60">
                <span>配单免邮费 (全岛配送)</span>
                {activeTab === 'pack2' && (
                  <span className="text-primary font-black bg-primary/10 px-2 py-0.5 rounded-md">比单盒购买省 SGD 16.00</span>
                )}
              </div>
            </div>

            {/* 套餐 Variant 选择 Tab */}
            <div className="space-y-3">
              <p className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">选择您的保养套餐</p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setActiveTab('pack2')}
                  className={`relative p-4 rounded-2xl text-left border-2 transition-all flex flex-col justify-between ${
                    activeTab === 'pack2'
                      ? 'border-primary bg-primary/5 ring-4 ring-primary/5'
                      : 'border-charcoal/10 bg-white hover:border-charcoal/30'
                  }`}
                >
                  {/* Popular 角标 */}
                  <span className="absolute -top-2.5 -right-1 bg-gradient-to-r from-primary to-primary-light text-charcoal-dark font-black text-[9px] px-2 py-0.5 rounded-full shadow-sm">
                    2盒免运送礼
                  </span>
                  <span className="text-sm font-black">14天常备装</span>
                  <span className="text-xs text-charcoal/60 mt-1">2 盒 · 14 袋</span>
                  <span className="text-sm font-black text-primary mt-3">SGD 79.80</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('pack1')}
                  className={`relative p-4 rounded-2xl text-left border-2 transition-all flex flex-col justify-between ${
                    activeTab === 'pack1'
                      ? 'border-primary bg-primary/5 ring-4 ring-primary/5'
                      : 'border-charcoal/10 bg-white hover:border-charcoal/30'
                  }`}
                >
                  <span className="text-sm font-black">7天启动装</span>
                  <span className="text-xs text-charcoal/60 mt-1">1 盒 · 7 袋</span>
                  <span className="text-sm font-black text-primary mt-3">SGD 47.90</span>
                </button>
              </div>
            </div>

            {/* 2 盒尊享五选一赠品选择框 */}
            {activeTab === 'pack2' && (
              <div className="space-y-3 bg-[#fcfaf5] p-5 rounded-2xl border border-charcoal/5 shadow-inner">
                <div className="flex items-center gap-1 text-xs font-bold text-primary uppercase tracking-wider">
                  <Award size={14} />
                  <span>2盒专享：赠送冷链法式鸡肉 1份 (五选一)</span>
                </div>
                <div className="space-y-2">
                  <label htmlFor="gift-select" className="sr-only">选择赠品</label>
                  <select
                    id="gift-select"
                    value={selectedGift}
                    onChange={(e) => setSelectedGift(e.target.value)}
                    className="w-full rounded-xl border border-charcoal/10 bg-white px-4 py-3.5 text-xs font-bold text-charcoal outline-none transition-all focus:border-primary"
                  >
                    {giftOptions.map(g => (
                      <option key={g.value} value={g.value}>{g.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* 高效成交双按钮 */}
            <div className="space-y-3 pt-2">
              {/* 主 CTA - WhatsApp 下单 */}
              <button
                type="button"
                onClick={handleWhatsAppOrder}
                className="w-full py-4.5 rounded-2xl bg-[#25D366] text-white font-bold hover:brightness-105 active:scale-[0.99] transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#25d366]/20 text-sm tracking-wide"
              >
                <MessageCircle fill="currentColor" size={18} />
                <span>WhatsApp 咨询并下单 (客服确认)</span>
              </button>

              {/* 辅助 CTA - PayNow 结账 */}
              <button
                type="button"
                onClick={handlePayNowSubmit}
                className="w-full py-4 rounded-2xl bg-charcoal text-ivory font-bold hover:bg-primary hover:text-charcoal-dark active:scale-[0.99] transition-all flex items-center justify-center gap-2 text-sm"
              >
                <span>直接 PayNow 付款下单</span>
                <ChevronRight size={16} />
              </button>
            </div>

            {/* 底部保障小字 */}
            <p className="text-[10px] text-center text-charcoal/30 leading-relaxed">
              * 新加坡官方旗舰店直接配送，现货库存 2-3 工作日送达。支持转账收据核对付款。
            </p>
          </div>
        </section>
      </main>

      {/* 尊贵品牌实力与黄梨酵素技术展示 */}
      <section className="bg-white py-16 border-y border-charcoal/5">
        <div className="max-w-7xl mx-auto px-4 md:px-8 grid gap-8 lg:grid-cols-2 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-extrabold text-primary tracking-wider uppercase">
              <Award size={12} />
              <span>为什么选择吃黄梨酵素长大的鸡？</span>
            </div>
            <h2 className="text-3xl font-black text-charcoal tracking-tight">
              把繁琐留给 70 天慢炼，<br />
              把“零负担”吸收留给身体。
            </h2>
            <p className="text-sm leading-7 text-charcoal/70">
              普通的熬煮鸡汤含有极高的油脂和高分子蛋白质，对于高压劳累、坐月子或术后恢复的敏感肠胃来说，常常伴随着难以消化和消化发胀的隐形负担。
            </p>
            <p className="text-sm leading-7 text-charcoal/70">
              Aqina 鸡只通过喂养由台湾 MD2 凤梨提取的天然活性酵素，帮助鸡只在成长过程中对蛋白质进行了良性的“预消化”，其鸡肉的天然氨基酸与小分子肽含量远高于普通鸡。我们通过 7 天双重滴存，彻底滤去多余油脂和腥味，滴滴纯净。喝下去的每一口，都是最纯粹、能被身体瞬间吸纳的满额元气。
            </p>
          </div>

          <div className="relative aspect-[4/3] rounded-3xl overflow-hidden border border-charcoal/5 shadow-lg">
            <Image
              src="/ugc/cozy-sofa.jpg"
              alt="Pineapple Enzyme Chicken Farm Source"
              fill
              className="object-cover"
            />
          </div>
        </div>
      </section>

      {/* 核心亮点：自制 Verified Reviews 评价秀墙 */}
      <section className="py-16 bg-[#faf8f5]">
        <div className="max-w-7xl mx-auto px-4 md:px-8 space-y-10">
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-extrabold text-primary tracking-wider uppercase">
              <ShieldCheck size={12} />
              <span>新加坡 Verified Buyers 真实好评</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black text-charcoal tracking-tight">
              328 位顾客的极佳口碑推荐
            </h2>
          </div>

          {/* 玻璃拟态卡片栅格 */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {VERIFIED_REVIEWS.map((review, i) => (
              <article 
                key={review.name} 
                className="bg-white rounded-3xl overflow-hidden border border-charcoal/5 shadow-md flex flex-col justify-between hover:shadow-lg transition-shadow duration-300"
              >
                {/* 顾客实景秀图 */}
                <div className="relative aspect-[16/10] w-full">
                  <Image 
                    src={review.image} 
                    alt={`${review.name} Real Purchase Review`} 
                    fill 
                    className="object-cover"
                  />
                  {/* 绿色 Verified 徽章 */}
                  <div className="absolute bottom-4 right-4 bg-green-600 text-white font-bold px-3 py-1 rounded-full text-[10px] shadow-sm tracking-wider flex items-center gap-1 uppercase">
                    <ShieldCheck size={11} fill="currentColor" />
                    <span>SG 已验买家</span>
                  </div>
                </div>

                <div className="p-6 space-y-4 flex-1 flex flex-col justify-between">
                  <p className="text-xs leading-relaxed text-charcoal/70 italic">
                    “{review.content}”
                  </p>

                  <div className="border-t border-charcoal/5 pt-4 flex items-center gap-3">
                    <div className="relative w-10 h-10 rounded-full overflow-hidden border border-primary/20">
                      <Image src={review.avatar} alt={review.name} fill className="object-cover" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-extrabold text-sm text-charcoal">{review.name}</span>
                        <div className="flex text-amber-400">
                          {Array.from({ length: 5 }).map((_, idx) => (
                            <Star key={idx} size={10} fill="currentColor" className="text-amber-400" />
                          ))}
                        </div>
                      </div>
                      <span className="text-[10px] text-charcoal/45 block">{review.role}</span>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* 极简 FAQ 常问问答 */}
      <section className="py-16 bg-white border-t border-charcoal/5">
        <div className="max-w-3xl mx-auto px-4 md:px-8 space-y-10">
          <h2 className="text-3xl font-black text-center text-charcoal tracking-tight">常见问答 (FAQ)</h2>
          <div className="space-y-6">
            {FAQ_ITEMS.map(item => (
              <div key={item.q} className="bg-[#faf8f5] p-6 rounded-2xl border border-charcoal/5 space-y-2">
                <div className="flex gap-2.5 items-start">
                  <HelpCircle className="text-primary mt-0.5 shrink-0" size={18} />
                  <h3 className="font-extrabold text-base text-charcoal">{item.q}</h3>
                </div>
                <div className="pl-7">
                  <p className="text-sm leading-relaxed text-charcoal/70">{item.a}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Checkout 结账模态框 */}
      {activeProduct && (
        <CheckoutModal
          isOpen={isCheckoutOpen}
          onClose={closeCheckout}
          product={selectedProduct}
        />
      )}
    </div>
  );
}
