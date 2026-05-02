"use client";

import type { ElementType, ReactNode } from "react";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type MotionTag =
  | "div"
  | "article"
  | "aside"
  | "figure"
  | "li"
  | "p"
  | "section"
  | "span"
  | "ul";

const motionTags = {
  div: motion.div,
  article: motion.article,
  aside: motion.aside,
  figure: motion.figure,
  li: motion.li,
  p: motion.p,
  section: motion.section,
  span: motion.span,
  ul: motion.ul,
} as const;

const easeOut = [0.22, 1, 0.36, 1] as const;
const reducedMotionQuery = "(prefers-reduced-motion: reduce)";

interface V2MotionBaseProps {
  as?: MotionTag;
  children: ReactNode;
  className?: string;
}

interface RevealProps extends V2MotionBaseProps {
  delay?: number;
  duration?: number;
  margin?: string;
  once?: boolean;
  rotate?: number;
  scale?: number;
  viewportAmount?: number;
  x?: number;
  y?: number;
}

interface StaggerGroupProps extends V2MotionBaseProps {
  delayChildren?: number;
  margin?: string;
  once?: boolean;
  staggerChildren?: number;
  viewportAmount?: number;
}

interface MotionItemProps extends V2MotionBaseProps {
  rotate?: number;
  scale?: number;
  x?: number;
  y?: number;
}

function StaticTag({
  as = "div",
  children,
  className,
}: V2MotionBaseProps) {
  const Component = as as ElementType<{
    children: ReactNode;
    className?: string;
  }>;

  return <Component className={className}>{children}</Component>;
}

export function useV2ReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(true);

  useEffect(() => {
    const mediaQuery = window.matchMedia(reducedMotionQuery);
    const updatePreference = () => {
      setPrefersReducedMotion(mediaQuery.matches);
    };

    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);

    return () => {
      mediaQuery.removeEventListener("change", updatePreference);
    };
  }, []);

  return prefersReducedMotion;
}

export function Reveal({
  as = "div",
  children,
  className,
  delay = 0,
  duration = 0.72,
  margin = "-72px",
  once = true,
  rotate = 0,
  scale = 0.98,
  viewportAmount = 0.18,
  x = 0,
  y = 24,
}: RevealProps) {
  const shouldReduceMotion = useV2ReducedMotion();

  if (shouldReduceMotion) {
    return (
      <StaticTag as={as} className={className}>
        {children}
      </StaticTag>
    );
  }

  const Component = motionTags[as] as typeof motion.div;

  return (
    <Component
      initial={{ opacity: 0, rotate, scale, x, y }}
      whileInView={{ opacity: 1, rotate: 0, scale: 1, x: 0, y: 0 }}
      viewport={{ once, amount: viewportAmount, margin }}
      transition={{ duration, ease: easeOut, delay }}
      className={className}
    >
      {children}
    </Component>
  );
}

export function StaggerGroup({
  as = "div",
  children,
  className,
  delayChildren = 0.08,
  margin = "-72px",
  once = true,
  staggerChildren = 0.1,
  viewportAmount = 0.16,
}: StaggerGroupProps) {
  const shouldReduceMotion = useV2ReducedMotion();

  if (shouldReduceMotion) {
    return (
      <StaticTag as={as} className={className}>
        {children}
      </StaticTag>
    );
  }

  const Component = motionTags[as] as typeof motion.div;

  return (
    <Component
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: viewportAmount, margin }}
      variants={{
        hidden: {},
        visible: {
          transition: {
            delayChildren,
            staggerChildren,
          },
        },
      }}
      className={className}
    >
      {children}
    </Component>
  );
}

export function MotionItem({
  as = "div",
  children,
  className,
  rotate = 0,
  scale = 0.98,
  x = 0,
  y = 22,
}: MotionItemProps) {
  const shouldReduceMotion = useV2ReducedMotion();

  if (shouldReduceMotion) {
    return (
      <StaticTag as={as} className={className}>
        {children}
      </StaticTag>
    );
  }

  const Component = motionTags[as] as typeof motion.div;

  return (
    <Component
      variants={{
        hidden: { opacity: 0, rotate, scale, x, y },
        visible: {
          opacity: 1,
          rotate: 0,
          scale: 1,
          x: 0,
          y: 0,
          transition: { duration: 0.66, ease: easeOut },
        },
      }}
      className={className}
    >
      {children}
    </Component>
  );
}
