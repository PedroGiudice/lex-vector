import React from 'react';

interface LineItem {
  description: string;
  amount: number;
  taskCode?: string;
  activityCode?: string;
}

interface LineItemEditorProps {
  items: LineItem[];
  onChange: (items: LineItem[]) => void;
  unitCost: number;
  disabled?: boolean;
}

const TASK_CODES = [
  { code: 'L100', label: 'Case Assessment' },
  { code: 'L110', label: 'Fact Investigation' },
  { code: 'L120', label: 'Analysis/Strategy' },
  { code: 'L160', label: 'Settlement/ADR' },
  { code: 'L210', label: 'Pleadings' },
  { code: 'L250', label: 'Motions' },
  { code: 'L320', label: 'Trial/Hearing' },
  { code: 'L510', label: 'Appeals' },
];

const ACTIVITY_CODES = [
  { code: 'A101', label: 'Plan/Prepare' },
  { code: 'A102', label: 'Research' },
  { code: 'A103', label: 'Draft/Revise' },
  { code: 'A104', label: 'Review/Analyze' },
  { code: 'A105', label: 'Appear/Attend' },
  { code: 'A106', label: 'Communicate' },
];

export const LineItemEditor: React.FC<LineItemEditorProps> = ({
  items,
  onChange,
  unitCost,
  disabled = false,
}) => {
  const updateItem = (index: number, updates: Partial<LineItem>) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], ...updates };
    onChange(newItems);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const addItem = () => {
    onChange([...items, { description: '', amount: 0 }]);
  };

  const total = items.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider font-['Manrope']">
          Line Items ({items.length})
        </h3>
        <button
          onClick={addItem}
          disabled={disabled}
          className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider bg-teal-500 text-black rounded-sm hover:bg-teal-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          + Add Item
        </button>
      </div>

      {/* Items */}
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {items.map((item, index) => (
          <div
            key={index}
            className="p-4 bg-[#121214] border border-zinc-800 rounded-sm space-y-3 hover:border-zinc-700 transition-colors"
          >
            {/* Row 1: Description + Amount + Delete */}
            <div className="flex gap-3">
              <input
                type="text"
                value={item.description}
                onChange={(e) => updateItem(index, { description: e.target.value })}
                placeholder="Service description..."
                disabled={disabled}
                className="flex-1 bg-zinc-900 border border-zinc-800 rounded-sm px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-violet-500 disabled:opacity-50 font-['Manrope']"
              />
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 text-sm">
                  $
                </span>
                <input
                  type="number"
                  value={item.amount || ''}
                  onChange={(e) => updateItem(index, { amount: parseFloat(e.target.value) || 0 })}
                  placeholder="0.00"
                  disabled={disabled}
                  className="w-28 bg-zinc-900 border border-zinc-800 rounded-sm pl-7 pr-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500 disabled:opacity-50 font-['JetBrains_Mono']"
                />
              </div>
              <button
                onClick={() => removeItem(index)}
                disabled={disabled || items.length <= 1}
                className="px-3 py-2 text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-sm transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title="Remove item"
              >
                <svg viewBox="0 0 24 24" fill="none" width={16} height={16}>
                  <path
                    d="M3 6H21"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="square"
                  />
                  <path
                    d="M19 6V21H5V6"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="square"
                  />
                  <rect x="9" y="3" width="6" height="3" stroke="currentColor" strokeWidth="2.5" />
                </svg>
              </button>
            </div>

            {/* Row 2: Task Code + Activity Code + Hours */}
            <div className="flex gap-3">
              <select
                value={item.taskCode || ''}
                onChange={(e) => updateItem(index, { taskCode: e.target.value || undefined })}
                disabled={disabled}
                className="flex-1 bg-zinc-900 border border-zinc-800 rounded-sm px-3 py-2 text-xs text-zinc-300 outline-none focus:border-violet-500 disabled:opacity-50"
              >
                <option value="">Auto Task Code</option>
                {TASK_CODES.map((tc) => (
                  <option key={tc.code} value={tc.code}>
                    {tc.code} - {tc.label}
                  </option>
                ))}
              </select>

              <select
                value={item.activityCode || ''}
                onChange={(e) => updateItem(index, { activityCode: e.target.value || undefined })}
                disabled={disabled}
                className="flex-1 bg-zinc-900 border border-zinc-800 rounded-sm px-3 py-2 text-xs text-zinc-300 outline-none focus:border-violet-500 disabled:opacity-50"
              >
                <option value="">Auto Activity Code</option>
                {ACTIVITY_CODES.map((ac) => (
                  <option key={ac.code} value={ac.code}>
                    {ac.code} - {ac.label}
                  </option>
                ))}
              </select>

              <div className="w-24 flex items-center justify-end text-xs text-zinc-500 font-['JetBrains_Mono']">
                {unitCost > 0 && item.amount > 0
                  ? `${(item.amount / unitCost).toFixed(2)} hrs`
                  : '-- hrs'}
              </div>
            </div>
          </div>
        ))}

        {items.length === 0 && (
          <div className="p-8 text-center text-zinc-600 text-sm border border-dashed border-zinc-800 rounded-sm">
            No line items. Click "Add Item" to start.
          </div>
        )}
      </div>

      {/* Footer: Total */}
      <div className="flex justify-between items-center pt-3 border-t border-zinc-800">
        <span className="text-xs text-zinc-500 uppercase tracking-wider">Total</span>
        <div className="flex items-center gap-4">
          <span className="text-lg font-bold text-teal-400 font-['JetBrains_Mono']">
            ${total.toFixed(2)}
          </span>
          {unitCost > 0 && (
            <span className="text-xs text-zinc-500 font-['JetBrains_Mono']">
              ({(total / unitCost).toFixed(2)} hrs)
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LineItemEditor;
