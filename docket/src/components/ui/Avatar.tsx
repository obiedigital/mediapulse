import clsx from 'clsx';

export function Avatar({ initials, color = 'bg-navy-800', size = 32 }: { initials: string; color?: string; size?: number }) {
  return (
    <div
      className={clsx('flex items-center justify-center rounded-full font-bold text-white shrink-0', color)}
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials}
    </div>
  );
}
