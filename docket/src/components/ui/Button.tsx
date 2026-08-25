import type { ButtonHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

type Variant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
  iconRight?: ReactNode;
}

const variants: Record<Variant, string> = {
  primary: 'bg-navy-800 text-white hover:bg-navy-700 shadow-sm shadow-navy-900/20',
  secondary: 'bg-gold-500 text-navy-950 hover:bg-gold-400 shadow-sm shadow-gold-600/20',
  ghost: 'bg-transparent text-ink hover:bg-navy-50',
  outline: 'bg-surface border border-line text-ink hover:border-navy-600/40 hover:bg-navy-50',
  danger: 'bg-danger-600 text-white hover:brightness-110',
};

const sizes: Record<Size, string> = {
  sm: 'text-[12.5px] px-3 py-1.5 rounded-lg gap-1.5',
  md: 'text-[13.5px] px-4 py-2.5 rounded-lg gap-2',
  lg: 'text-[15px] px-5 py-3 rounded-xl gap-2',
};

export function Button({ variant = 'primary', size = 'md', icon, iconRight, className, children, ...rest }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center font-semibold whitespace-nowrap transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none',
        variants[variant],
        sizes[size],
        className
      )}
      {...rest}
    >
      {icon}
      {children}
      {iconRight}
    </button>
  );
}
