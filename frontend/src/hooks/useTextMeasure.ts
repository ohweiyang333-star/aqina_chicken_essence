'use client'

import { useEffect, useState, useRef } from 'react'
import { prepare, layout, type PreparedText } from '@chenglou/pretext'

/**
 * 使用 Pretext 测量文本高度的 Hook
 *
 * @param text - 要测量的文本
 * @param maxWidth - 最大宽度（px）
 * @param font - CSS 字体简写（如 '16px Inter'）
 * @param lineHeight - 行高（px）
 * @returns { height, lineCount } - 文本高度和行数
 */
export function useTextMeasure(
  text: string,
  maxWidth: number,
  font: string,
  lineHeight: number
) {
  const [dimensions, setDimensions] = useState<{ height: number; lineCount: number }>({
    height: 0,
    lineCount: 0,
  })
  const preparedRef = useRef<PreparedText | null>(null)

  useEffect(() => {
    // 一次性准备（较慢）
    preparedRef.current = prepare(text, font)
  }, [text, font])

  useEffect(() => {
    if (preparedRef.current) {
      // 快速计算（极快）
      const result = layout(preparedRef.current, maxWidth, lineHeight)
      setDimensions(result)
    }
  }, [maxWidth, lineHeight])

  return dimensions
}

/**
 * 使用 Pretext 测量多段文本的 Hook
 * 适用于产品描述、客户评价等多段落内容
 *
 * @param texts - 文本数组
 * @param maxWidth - 最大宽度（px）
 * @param font - CSS 字体简写
 * @param lineHeight - 行高（px）
 * @returns 总高度和各段高度
 */
export function useMultiTextMeasure(
  texts: string[],
  maxWidth: number,
  font: string,
  lineHeight: number
) {
  const [totalHeight, setTotalHeight] = useState(0)
  const [individualHeights, setIndividualHeights] = useState<number[]>([])
  const preparedListRef = useRef<PreparedText[]>([])

  // 准备所有文本
  useEffect(() => {
    preparedListRef.current = texts.map((t) => prepare(t, font))
  }, [texts, font])

  // 计算所有高度
  useEffect(() => {
    const heights = preparedListRef.current.map((p) => layout(p, maxWidth, lineHeight).height)
    setIndividualHeights(heights)
    setTotalHeight(heights.reduce((sum, h) => sum + h, 0))
  }, [maxWidth, lineHeight])

  return { totalHeight, individualHeights }
}
