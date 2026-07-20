"use client";

export function EditableField({
  label,
  multiline = false,
  onSave,
  value,
}: {
  label: string;
  multiline?: boolean;
  onSave: (value: string) => void;
  value: string;
}) {
  const sharedClassName =
    "w-full rounded-[14px] border border-[#e4dacd] bg-[#fffdfa] px-3.5 py-3 text-sm leading-6 text-[#1b1916] shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] outline-none transition-colors duration-150 focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]";

  return (
    <label className="block">
      <span className="mb-2 block text-[0.64rem] tracking-[0.18em] text-[#7c6d58] uppercase">
        {label}
      </span>
      {multiline ? (
        <textarea
          key={`${label}:${value}`}
          rows={4}
          defaultValue={value}
          onBlur={(event) => {
            const nextValue = event.currentTarget.value;
            if (nextValue !== value) {
              onSave(nextValue);
            }
          }}
          className={sharedClassName}
        />
      ) : (
        <input
          key={`${label}:${value}`}
          defaultValue={value}
          onBlur={(event) => {
            const nextValue = event.currentTarget.value;
            if (nextValue !== value) {
              onSave(nextValue);
            }
          }}
          className={sharedClassName}
        />
      )}
    </label>
  );
}

export function SelectField({
  label,
  onSave,
  options,
  value,
}: {
  label: string;
  onSave: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  value: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-[0.64rem] tracking-[0.18em] text-[#7c6d58] uppercase">
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onSave(event.currentTarget.value)}
        className="w-full rounded-[14px] border border-[#e4dacd] bg-[#fffdfa] px-3.5 py-3 text-sm leading-6 text-[#1b1916] shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] outline-none transition-colors duration-150 focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
