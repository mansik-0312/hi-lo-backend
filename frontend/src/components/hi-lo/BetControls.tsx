"use client";

interface BetControlsProps {
  betAmount: number;
  minBet: number;
  maxBet: number;
  disabled: boolean;
  onChange: (amount: number) => void;
}

export default function BetControls({
  betAmount,
  minBet,
  maxBet,
  disabled,
  onChange,
}: BetControlsProps) {
  const decrease = () => {
    onChange(Math.max(minBet, Number((betAmount - 1).toFixed(2))));
  };

  const increase = () => {
    onChange(Math.min(maxBet, Number((betAmount + 1).toFixed(2))));
  };

  return (
    <div className="bet-controls">
      <div className="bet-header">
        <span className="bet-label">BET AMOUNT</span>
        <span className="bet-limits">
          Min {minBet.toFixed(2)} · Max {maxBet.toFixed(2)}
        </span>
      </div>

      <div className="bet-input">
        <button
          type="button"
          className="bet-button"
          onClick={decrease}
          disabled={disabled || betAmount <= minBet}
        >
          −
        </button>

        <div className="bet-value">
          <span className="bet-currency">$</span>
          <strong>{betAmount.toFixed(2)}</strong>
        </div>

        <button
          type="button"
          className="bet-button"
          onClick={increase}
          disabled={disabled || betAmount >= maxBet}
        >
          +
        </button>
      </div>

      <div className="bet-presets">
        {[1, 2, 5, 10].map((amount) => (
          <button
            key={amount}
            type="button"
            className="bet-preset"
            disabled={disabled || amount < minBet || amount > maxBet}
            onClick={() => onChange(amount)}
          >
            ${amount}
          </button>
        ))}
      </div>
    </div>
  );
}