// PlayingCard.tsx
import { Card } from "@/types/hilo";
import { suitSymbols } from "@/lib/api/suits";

interface PlayingCardProps {
  card: Card | null;
}

export default function PlayingCard({ card }: PlayingCardProps) {
  if (!card) {
    return (
      <div className="playing-card card-placeholder">
        <span>?</span>
      </div>
    );
  }

  const isRed = card.suit === "hearts" || card.suit === "diamonds";
  const symbol = suitSymbols[card.suit];

  return (
    <div className={`playing-card ${isRed ? "red" : "black"}`}>
      <div className="card-corner top">
        <strong className="card-rank">{card.rank}</strong>
        <span className="card-suit-small">{symbol}</span>
      </div>

      <div className="card-suit-large">{symbol}</div>

      <div className="card-corner bottom">
        <strong className="card-rank">{card.rank}</strong>
        <span className="card-suit-small">{symbol}</span>
      </div>
    </div>
  );
}