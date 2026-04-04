# Aqina Homepage Rebuild 实施计划

> **代理工作者：** 必需的子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 来逐步实施此计划。步骤使用复选框（`- [ ]`）语法进行跟踪。

**目标：** 将首页展示层重建为参考稿的深绿金色高转化风格，同时保持现有多语言、产品读取、购物车和下单链路不变。

**架构：** 以 `src/app/[locale]/page.tsx` 继续作为数据和交互编排层，只重建首页展示组件与样式层。保留 `getProducts()`、`useCartStore`、`CheckoutModal` 和 `CartDrawer` 的既有接口，通过新的组件组合和翻译键实现参考稿结构。

**技术栈：** Next.js 16, React 19, Tailwind CSS v4, next-intl, Zustand, Firebase/Firestore

---

### 任务 1：建立新的首页视觉系统

**文件：**
- 修改：`src/app/[locale]/layout.tsx`
- 修改：`src/app/globals.css`

- [ ] **步骤 1：更新全局字体与页面根样式**

在 `src/app/[locale]/layout.tsx` 中：
- 将 Google Fonts 从 `Outfit + Inter` 改为 `Cormorant_Garamond + Plus_Jakarta_Sans`
- 保留 `NextIntlClientProvider`
- 保留 `Header` 与 `WhatsAppButton` 的挂载位置

在 `src/app/globals.css` 中：
- 重建主题变量为深绿、表面绿、金色、黄色 CTA、浅文字、 muted 文字
- 定义 heading/body 字体变量
- 加入滚动、section 容器、gold text、gold border、premium shadow、mobile safe area 等复用工具类

- [ ] **步骤 2：运行 lint 检查根样式与字体导入**

运行：`npm run lint`
预期：无新增 ESLint 错误

### 任务 2：重建 Header 与移动端辅助动作

**文件：**
- 修改：`src/components/Header.tsx`
- 修改：`src/components/WhatsAppButton.tsx`
- 创建：`src/components/MobileFloatingCTA.tsx`

- [ ] **步骤 1：重写 Header 为参考稿固定头部**

在 `src/components/Header.tsx`：
- 保留 `useCartStore`、`initializeCart()`、`CartDrawer`
- 删除桌面导航、语言切换、移动菜单抽屉 UI
- 保留购物车按钮与数量 badge
- 改为深色半透明固定头部和更简化的 Aqina 品牌样式

- [ ] **步骤 2：新增移动端底部 CTA**

在 `src/components/MobileFloatingCTA.tsx`：
- 新建仅移动端显示的底部 CTA
- 支持通过锚点跳转到 `#products`
- 使用翻译键渲染按钮文本

- [ ] **步骤 3：调整 WhatsApp 浮钮避免与底部 CTA 冲突**

在 `src/components/WhatsAppButton.tsx`：
- 保留跳转行为
- 调整移动端 bottom/right 偏移
- 保持桌面端可读标签，移动端压缩尺寸

- [ ] **步骤 4：运行 lint**

运行：`npm run lint`
预期：无新增 ESLint 错误

### 任务 3：重建首页主内容组件

**文件：**
- 创建：`src/components/IdentitySelector.tsx`
- 修改：`src/components/HeroSection.tsx`
- 创建：`src/components/TargetAudienceSection.tsx`
- 修改：`src/components/ScienceEndorsementSection.tsx`
- 修改：`src/components/Footer.tsx`

- [ ] **步骤 1：新增 IdentitySelector**

在 `src/components/IdentitySelector.tsx`：
- 创建横向滚动按钮条
- 提供 4 个本地锚点：workplace、maternity、halal、recovery
- 使用 Material Symbols 或现有图标系统表达身份类型

- [ ] **步骤 2：重写 HeroSection**

在 `src/components/HeroSection.tsx`：
- 重建为大图背景 + 叠层渐变 + 金色标题
- 保留 CTA 到产品区的跳转
- 使用本地化文案，不引入新数据请求

- [ ] **步骤 3：新增 TargetAudienceSection**

在 `src/components/TargetAudienceSection.tsx`：
- 创建 4 个 audience blocks
- 处理交替布局、嵌套图片网格、金色标题和段落
- 使用翻译键输出文案
- 只使用本地静态图片路径或现有图片资源

- [ ] **步骤 4：重构 ScienceEndorsementSection**

在 `src/components/ScienceEndorsementSection.tsx`：
- 保留信任与认证叙事
- 改造成与参考稿一致的深色高级区块

- [ ] **步骤 5：重构 Footer**

在 `src/components/Footer.tsx`：
- 简化为品牌、导航、版权
- 使用新视觉风格

- [ ] **步骤 6：运行 lint**

运行：`npm run lint`
预期：无新增 ESLint 错误

### 任务 4：重建价格卡但保留现有产品逻辑

**文件：**
- 修改：`src/components/ProductPricingSection.tsx`
- 修改：`src/components/ProductCard.tsx`

- [ ] **步骤 1：重构 ProductPricingSection 外层布局**

在 `src/components/ProductPricingSection.tsx`：
- 改为深色背景中的 4 列 premium pricing grid
- 保留 `products`, `isLoading`, `onAddToCart`, `onBuyNow` props
- 保留 loading skeleton 分支

- [ ] **步骤 2：重构 ProductCard**

在 `src/components/ProductCard.tsx`：
- 使用金色边框和推荐款放大/强调样式
- 保持当前 `DisplayProduct` 字段消费方式
- 保持两个按钮分别调用 `onAddToCart(product)` 与 `onBuyNow(product)`

- [ ] **步骤 3：运行 lint**

运行：`npm run lint`
预期：无新增 ESLint 错误

### 任务 5：重新编排首页并补齐多语言文案

**文件：**
- 修改：`src/app/[locale]/page.tsx`
- 修改：`messages/en.json`
- 修改：`messages/zh.json`

- [ ] **步骤 1：调整首页组件顺序**

在 `src/app/[locale]/page.tsx`：
- 保留现有 `getProducts()`、fallback product、`handleAddToCart`、`handleBuyNow`
- 引入并挂载：
  - `IdentitySelector`
  - `TargetAudienceSection`
  - `MobileFloatingCTA`
- 移除首页中的：
  - `StorySection`
  - `PolicySection`
  - `ProblemSolutionSection`
  - `TestimonialsSection`
  - `FAQSection`
- 保留 `CheckoutModal` 与 `Footer`

- [ ] **步骤 2：扩展双语文案**

在 `messages/en.json` 和 `messages/zh.json`：
- 新增 identity selector 文案
- 新增 target audience 文案
- 新增 mobile CTA 文案
- 调整 hero/science/footer/products 文案以适配新结构
- 保持键结构一致

- [ ] **步骤 3：运行 lint**

运行：`npm run lint`
预期：无新增 ESLint 错误

### 任务 6：验证 UI 与关键业务链路

**文件：**
- 无代码新增，验证已有改动

- [ ] **步骤 1：执行生产构建**

运行：`npm run build`
预期：Next.js 生产构建成功

- [ ] **步骤 2：手动检查首页关键链路**

运行：`npm run dev`
预期：本地首页可访问

手动验证：
- 英文首页可正常渲染
- 中文首页可正常渲染
- Header 购物车可打开 `CartDrawer`
- 产品卡 `Add to Cart` 仍可加入购物车
- 产品卡 `Buy Now` 仍可打开 `CheckoutModal`
- Checkout 表单仍可提交到既有下单逻辑
- 移动端底部 CTA 与 WhatsApp 浮钮不重叠

- [ ] **步骤 3：整理改动并准备交付说明**

输出：
- 修改摘要
- 验证结果
- 残余风险（如果有）
