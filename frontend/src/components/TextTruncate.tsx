'use client'

import { useTextMeasure } from '@/hooks/useTextMeasure'

interface TextTruncateProps {
  text: string
  maxWidth: number
  font?: string
  lineHeight?: number
  maxLines?: number
  showMoreLabel?: string
  showLessLabel?: string
  className?: string
}

/**
 * 智能文本截断组件
 * 使用 Pretext 预计算高度，无需 DOM 测量
 *
 * 适用场景：
 * - 产品描述（显示前 N 行，点击展开）
 * - 客户评价（长文本截断）
 * - FAQ 回答
 */
export function TextTruncate({
  text,
  maxWidth,
  font = '16px Inter',
  lineHeight = 24,
  maxLines = 3,
  showMoreLabel = '显示更多',
  showLessLabel = '收起',
  className = '',
}: TextTruncateProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { height, lineCount } = useTextMeasure(text, maxWidth, font, lineHeight)

  const maxHeight = lineHeight * maxLines
  const shouldTruncate = lineCount > maxLines

  return (
    <div className={className}>
      <div
        style={{
          overflow: 'hidden',
          height: isExpanded ? height : maxHeight,
          transition: 'height 0.3s ease',
        }}
      >
        <p style={{ font, lineHeight: `${lineHeight}px`, margin: 0 }}>
          {text}
        </p>
      </div>

      {shouldTruncate && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 text-sm text-blue-600 hover:text-blue-800 transition-colors"
        >
          {isExpanded ? showLessLabel : showMoreLabel}
        </button>
      )}
    </div>
  )
}

import { useState } from 'react'
