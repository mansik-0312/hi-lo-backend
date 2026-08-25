"use client";

import { Round } from "@/types/hilo";
import { suitSymbols } from "@/lib/api/suits";

interface RoundHistoryProps {
  rounds: Round[];
}

export default function RoundHistory({ rounds }: RoundHistoryProps) {
  if (!rounds.length) {
    return (
      <div className="round-history-empty">
        <span>♠</span>
        <p>No rounds played yet.</p>
      </div>
    );
  }

  return (
    <div className="round-history">
      {rounds.map((round) => {
        const previousSuit = suitSymbols[round.previous_card.suit];
        const nextSuit = suitSymbols[round.next_card.suit];

        return (
          <div className="round-row" key={round.round_id}>
            <div className="round-number">#{round.round_number}</div>

            <div className="round-cards">
              {round.previous_card.rank}
              {previousSuit}
              <span>→</span>
              {round.next_card.rank}
              {nextSuit}
            </div>

            <div className="round-prediction">{round.prediction}</div>

            <div className={`round-result ${round.result}`}>
              {round.result}
            </div>

            <div className={`round-payout ${round.result}`}>
              {round.payout > 0
                ? `+$${round.payout.toFixed(2)}`
                : `-$${round.bet_amount.toFixed(2)}`}
            </div>
          </div>
        );
      })}
    </div>
  );
}