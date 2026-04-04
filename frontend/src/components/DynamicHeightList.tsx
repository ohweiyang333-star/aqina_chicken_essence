'use client'

import { useMultiTextMeasure } from '@/hooks/useTextMeasure'

interface DynamicHeightListProps {
  items: Array<{
    id: string
    title: string
    description: string
  }>
  maxWidth: number
  titleFont?: string
  descFont?: string
  lineHeight?: number
}

/**
 * 动态高度列表组件
 * 使用 Pretext 预计算所有项目高度，实现平滑动画
 *
 * 适用场景：
 * - 产品列表（不同长度的描述）
 * - FAQ 列表
 * - 评价列表
 */
export function DynamicHeightList({
  items,
  maxWidth,
  titleFont = '18px Inter',
  descFont = '16px Inter',
  lineHeight = 24,
}: DynamicHeightListProps) {
  const titles = items.map((i) => i.title)
  const descriptions = items.map((i) => i.description)

  const { individualHeights: titleHeights } = useMultiTextMeasure(
    titles,
    maxWidth,
    titleFont,
    lineHeight
  )

  const { individualHeights: descHeights } = useMultiTextMeasure(
    descriptions,
    maxWidth,
    descFont,
    lineHeight
  )

  return (
    <div className="space-y-4">
      {items.map((item, index) => {
        const itemHeight = titleHeights[index] + descHeights[index] + lineHeight // 标题 + 描述 + 间距

        return (
          <div
            key={item.id}
            className="border rounded-lg p-4 transition-all duration-300 hover:shadow-md"
            style={{
              minHeight: itemHeight,
            }}
          >
            <h3 style={{ font: titleFont, lineHeight: `${lineHeight}px` }} className="font-semibold">
              {item.title}
            </h3>
            <p
              style={{ font: descFont, lineHeight: `${lineHeight}px` }}
              className="text-gray-600 mt-2"
            >
              {item.description}
            </p>
          </div>
        )
      })}
    </div>
  )
}
