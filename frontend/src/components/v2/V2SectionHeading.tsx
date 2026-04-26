interface V2SectionHeadingProps {
  eyebrow: string;
  title: string;
  body?: string;
  align?: "left" | "center";
}

export default function V2SectionHeading({
  eyebrow,
  title,
  body,
  align = "left",
}: V2SectionHeadingProps) {
  return (
    <div
      className={[
        "max-w-3xl space-y-4",
        align === "center" ? "mx-auto text-center" : "",
      ].join(" ")}
    >
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#9b6b1f]">
        {eyebrow}
      </p>
      <h2 className="font-heading text-4xl font-semibold leading-tight text-[#23170d] md:text-5xl">
        {title}
      </h2>
      {body ? (
        <p className="text-base leading-8 text-[#6f5a43] md:text-lg">{body}</p>
      ) : null}
    </div>
  );
}
