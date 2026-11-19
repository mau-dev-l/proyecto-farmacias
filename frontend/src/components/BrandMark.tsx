type BrandMarkProps = {
  /** Square size in pixels. The artwork scales with it. */
  size?: number
  className?: string
}

/**
 * Pharmacy brand mark: a capsule tilted -45° with an upright medical cross.
 *
 * The capsule inherits `currentColor` so it adapts to the sidebar, the login
 * hero and the light cards. The cross keeps the pharmacy green accent.
 */
export function BrandMark({ size = 28, className }: BrandMarkProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <g transform="rotate(-45 16 16)">
        <rect
          x="3"
          y="10.5"
          width="26"
          height="11"
          rx="5.5"
          fill="currentColor"
          fillOpacity="0.14"
          stroke="currentColor"
          strokeWidth="2"
        />
      </g>
      <path
        className="brand-mark-cross"
        d="M16 11.2v9.6M11.2 16h9.6"
        strokeWidth="2.8"
        strokeLinecap="round"
      />
    </svg>
  )
}
