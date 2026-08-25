"use client";

import { Prediction } from "@/types/hilo";

interface BettingPanelProps {
  betAmount: number;
  prediction: Prediction | null;
  loading: boolean;
  onBetAmountChange: (
    amount: number,
  ) => void;
  onPredictionChange: (
    prediction: Prediction,
  ) => void;
  onPlay: () => void;
}

export default function BettingPanel({
  betAmount,
  prediction,
  loading,
  onBetAmountChange,
  onPredictionChange,
  onPlay,
}: BettingPanelProps) {
  return (
    <div className="w-full max-w-xl space-y-5">
      <div>
        <label className="mb-2 block text-sm text-white/60">
          Bet Amount
        </label>

        <input
          type="number"
          min={1}
          max={100}
          step={0.01}
          value={betAmount}
          onChange={(event) =>
            onBetAmountChange(
              Number(event.target.value),
            )
          }
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition focus:border-white/30"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() =>
            onPredictionChange("higher")
          }
          className={`rounded-xl px-5 py-4 font-semibold transition ${
            prediction === "higher"
              ? "bg-emerald-500 text-white"
              : "bg-white/5 text-white/70 hover:bg-white/10"
          }`}
        >
          ↑ Higher
        </button>

        <button
          type="button"
          onClick={() =>
            onPredictionChange("lower")
          }
          className={`rounded-xl px-5 py-4 font-semibold transition ${
            prediction === "lower"
              ? "bg-rose-500 text-white"
              : "bg-white/5 text-white/70 hover:bg-white/10"
          }`}
        >
          ↓ Lower
        </button>
      </div>

      <button
        type="button"
        disabled={
          loading ||
          !prediction ||
          betAmount <= 0
        }
        onClick={onPlay}
        className="w-full rounded-xl bg-white px-5 py-4 font-bold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {loading
          ? "Revealing..."
          : "Play Round"}
      </button>
    </div>
  );
}