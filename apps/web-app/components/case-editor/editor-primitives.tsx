import type { ReactNode } from "react";

function IconShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`flex h-4 w-4 items-center justify-center ${className ?? ""}`}
    >
      {children}
    </span>
  );
}

export function PlusIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.8]">
        <path d="M8 3.25v9.5M3.25 8h9.5" strokeLinecap="round" />
      </svg>
    </IconShell>
  );
}

export function SparkIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.6]">
        <path d="M8 2.5 9.4 6.6 13.5 8l-4.1 1.4L8 13.5 6.6 9.4 2.5 8l4.1-1.4L8 2.5Z" />
      </svg>
    </IconShell>
  );
}

export function StopIcon() {
  return (
    <IconShell>
      <svg
        viewBox="0 0 16 16"
        className="h-4 w-4 fill-none stroke-current stroke-[1.6]"
      >
        <rect x="4.25" y="4.25" width="7.5" height="7.5" rx="1.2" />
      </svg>
    </IconShell>
  );
}

export function ArrowLeftIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.8]">
        <path d="M12.5 8H3.5M7 3.75 3 8l4 4.25" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </IconShell>
  );
}

export function CheckIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.8]">
        <path d="m3.5 8.2 2.7 2.7 6.3-6.1" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </IconShell>
  );
}

export function WarningIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.6]">
        <path d="M8 3.15 13 12H3L8 3.15Z" strokeLinejoin="round" />
        <path d="M8 6.3v2.9M8 11.15h.01" strokeLinecap="round" />
      </svg>
    </IconShell>
  );
}

export function ChevronDownIcon({
  className,
}: {
  className?: string;
}) {
  return (
    <IconShell className={className}>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.8]">
        <path d="m3.75 6 4.25 4 4.25-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </IconShell>
  );
}

export function CloseIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.8]">
        <path d="m4 4 8 8M12 4 4 12" strokeLinecap="round" />
      </svg>
    </IconShell>
  );
}

export function UndoIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.7]">
        <path d="M6.1 4.35 3.5 6.9l2.6 2.55" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M4 6.9h4.2c2.05 0 3.8 1.4 4.3 3.4" strokeLinecap="round" />
      </svg>
    </IconShell>
  );
}

export function JumpIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.7]">
        <path d="M5.5 10.5 10.5 5.5M6 5.5h4.5V10" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </IconShell>
  );
}

export function EyeIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.6]">
        <path d="M1.8 8s2.3-3.6 6.2-3.6S14.2 8 14.2 8s-2.3 3.6-6.2 3.6S1.8 8 1.8 8Z" />
        <circle cx="8" cy="8" r="1.8" />
      </svg>
    </IconShell>
  );
}

export function MoreIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-current">
        <circle cx="3.5" cy="8" r="1.2" />
        <circle cx="8" cy="8" r="1.2" />
        <circle cx="12.5" cy="8" r="1.2" />
      </svg>
    </IconShell>
  );
}

export function TrashIcon() {
  return (
    <IconShell>
      <svg viewBox="0 0 16 16" className="h-4 w-4 fill-none stroke-current stroke-[1.6]">
        <path d="M3.5 4.75h9" strokeLinecap="round" />
        <path d="M6.25 4.75V3.7c0-.5.4-.9.9-.9h1.7c.5 0 .9.4.9.9v1.05" />
        <path d="m5 4.75.55 7.1c.05.63.57 1.1 1.2 1.1h2.5c.63 0 1.15-.47 1.2-1.1L11 4.75" strokeLinecap="round" />
      </svg>
    </IconShell>
  );
}

export function SecondaryButton({
  ariaLabel,
  children,
  className,
  onClick,
  title,
}: {
  ariaLabel: string;
  children: ReactNode;
  className?: string;
  onClick: () => void;
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel}
      title={title ?? ariaLabel}
      className={`inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#d8ccbb] bg-[#fffdf8] text-[#2b251f] shadow-[0_10px_24px_rgba(54,42,23,0.08)] transition-all duration-150 hover:-translate-y-0.5 hover:bg-[#f8f0e4] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1] ${className ?? ""}`}
    >
      {children}
    </button>
  );
}

export function TextButton({
  children,
  className,
  disabled = false,
  onClick,
}: {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${className ?? ""}`}
    >
      {children}
    </button>
  );
}
