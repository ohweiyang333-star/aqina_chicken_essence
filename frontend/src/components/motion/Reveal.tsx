import type { ReactNode } from 'react';

/**
 * The page's single authored motion moment: content settles into place as it enters.
 *
 * Implemented as CSS scroll-driven animation (see `.reveal` in globals.css), deliberately
 * NOT as a JS animation library:
 *
 *  - The resting state is the DEFAULT. Without JS, without the animation API, or with
 *    reduced-motion on, every element renders fully visible. Nothing is ever hidden
 *    behind a script on a page whose whole job is to sell.
 *  - No requestAnimationFrame dependency, so a backgrounded/throttled tab cannot strand
 *    content at opacity 0.
 *
 * `index` staggers siblings by shifting the animation range slightly.
 */

interface RevealProps {
  children: ReactNode;
  className?: string;
  /** Stagger position within a group. */
  index?: number;
  as?: 'div' | 'section' | 'li' | 'article' | 'figure' | 'ol' | 'ul' | 'dl';
}

function revealClass(className?: string) {
  return className ? `reveal ${className}` : 'reveal';
}

/** Stagger by nudging the entry range; capped so late items never lag noticeably. */
function staggerStyle(index?: number) {
  if (!index) return undefined;
  const step = Math.min(index, 6) * 4;
  return { '--reveal-offset': `${step}%` } as React.CSSProperties;
}

export function Reveal({ children, className, index, as = 'div' }: RevealProps) {
  const Tag = as;
  return (
    <Tag className={revealClass(className)} style={staggerStyle(index)}>
      {children}
    </Tag>
  );
}

/**
 * Group wrapper. Purely structural — the stagger lives on the items, so a group that
 * fails to render still leaves its children visible.
 */
export function RevealGroup({
  children,
  className,
  as = 'div',
}: {
  children: ReactNode;
  className?: string;
  as?: 'div' | 'ul' | 'ol' | 'dl';
}) {
  const Tag = as;
  return <Tag className={className}>{children}</Tag>;
}

export function RevealItem({
  children,
  className,
  index,
  as = 'div',
}: {
  children: ReactNode;
  className?: string;
  index?: number;
  as?: 'div' | 'li' | 'article' | 'figure';
}) {
  const Tag = as;
  return (
    <Tag className={revealClass(className)} style={staggerStyle(index)}>
      {children}
    </Tag>
  );
}
