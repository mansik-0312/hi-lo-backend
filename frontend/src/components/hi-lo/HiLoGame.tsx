"use client";

import { useEffect, useState } from "react";

import {
  getGame,
  getRoundHistory,
  playRound,
  startGame,
} from "@/lib/api/hilo";

import {
  Card,
  Prediction,
  Round,
} from "@/types/hilo";

import PlayingCard from "./PlayingCard";
import BetControls from "./BetControls";
import RoundHistory from "./RoundHistory";

const INITIAL_BALANCE = 10;
const MIN_BET = 1;
const MAX_BET = 100;

export default function HiLoGame() {
  const [gameId, setGameId] = useState<string | null>(
    null,
  );

  const [card, setCard] = useState<Card | null>(null);

  const [previousCard, setPreviousCard] =
    useState<Card | null>(null);

  const [nextCard, setNextCard] =
    useState<Card | null>(null);

  const [balance, setBalance] = useState(
    INITIAL_BALANCE,
  );

  const [betAmount, setBetAmount] =
    useState(MIN_BET);

  const [rounds, setRounds] = useState<Round[]>([]);

  const [result, setResult] = useState<
    "win" | "loss" | "push" | null
  >(null);

  const [payout, setPayout] = useState(0);

  const [loading, setLoading] = useState(true);

  const [playing, setPlaying] = useState(false);

  const [error, setError] = useState<string | null>(
    null,
  );

  const [cardAnimating, setCardAnimating] =
    useState(false);

  async function initializeGame() {
    try {
      setLoading(true);
      setError(null);

      const game = await startGame(
        INITIAL_BALANCE,
      );

      setGameId(game.game_id);
      setCard(game.current_card);
      setBalance(Number(game.balance));

      const history =
        await getRoundHistory(0, 20);

      setRounds(history.rounds);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to start game.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    initializeGame();
  }, []);

async function handlePlay(prediction: Prediction) {
if (!gameId || playing || balance < betAmount) {
    return;
}

try {
    setPlaying(true);
    setError(null);
    setResult(null);

    setPreviousCard(card);
    setNextCard(null);

    const response = await playRound(gameId, {
    bet_amount: betAmount,
    prediction,
    });

    setNextCard(response.next_card);
    setBalance(Number(response.balance));
    setPayout(Number(response.payout));
    setResult(response.result);

    // Start card reveal
    setCardAnimating(true);

    window.setTimeout(() => {
    setCard(response.next_card);
    setCardAnimating(false);
    setPreviousCard(null);
    setNextCard(null);
    }, 600);

    const history = await getRoundHistory(0, 20);

    setRounds(history.rounds);
} catch (err) {
    setError(
    err instanceof Error
        ? err.message
        : "Unable to play round."
    );
} finally {
    setPlaying(false);
}
}
  async function refreshGame() {
    if (!gameId) {
      return;
    }

    try {
      const game = await getGame(gameId);

      setCard(game.current_card);
      setBalance(Number(game.balance));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to refresh game.",
      );
    }
  }

  if (loading) {
    return (
      <main className="game-shell">
        <div className="game-loading">
          <div className="loading-spinner" />
          <p>Preparing your table...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="game-shell">
      <div className="game-container">

        {/* HEADER */}

        <header className="game-header">
          <div>
            <div className="brand-mark">
              HI<span>•</span>LO
            </div>

            <p className="game-subtitle">
              Predict the next card
            </p>
          </div>

          <div className="balance-card">
            <span>YOUR BALANCE</span>
            <strong>
              ${balance.toFixed(2)}
            </strong>
          </div>
        </header>

        {/* GAME TABLE */}

        <section className="game-table">

          <div className="table-glow" />

          <div className="game-status">
            <span className="live-dot" />
            LIVE GAME
          </div>

          <div className="card-stage">

            <div className="card-label">
              CURRENT CARD
            </div>

            <div
              className={
                cardAnimating
                  ? "card-wrapper reveal"
                  : "card-wrapper"
              }
            >
              <PlayingCard card={card} />
            </div>

            {card && (
              <div className="card-value">
                {card.rank}{" "}
                <span>
                  {card.suit}
                </span>
              </div>
            )}
          </div>

          <div className="prediction-divider">
            <span />
            <div>WHAT'S NEXT?</div>
            <span />
          </div>

          {/* PREDICTIONS */}

          <div className="prediction-buttons">

            <button
              className="prediction-button higher"
              disabled={
                playing ||
                balance < betAmount
              }
              onClick={() =>
                handlePlay("higher")
              }
            >
              <span className="prediction-icon">
                ↑
              </span>

              <span className="prediction-content">
                <strong>HIGHER</strong>
                <small>
                  Next card is higher
                </small>
              </span>
            </button>

            <button
              className="prediction-button lower"
              disabled={
                playing ||
                balance < betAmount
              }
              onClick={() =>
                handlePlay("lower")
              }
            >
              <span className="prediction-icon">
                ↓
              </span>

              <span className="prediction-content">
                <strong>LOWER</strong>
                <small>
                  Next card is lower
                </small>
              </span>
            </button>

          </div>

          {/* BET */}

          <BetControls
            betAmount={betAmount}
            minBet={MIN_BET}
            maxBet={MAX_BET}
            disabled={playing}
            onChange={setBetAmount}
          />

          {/* RESULT */}

          {result && (
            <div
              className={`result-banner ${result}`}
            >
              <div className="result-title">
                {result === "win" &&
                  "YOU WIN!"}

                {result === "loss" &&
                  "BET LOST"}

                {result === "push" &&
                  "PUSH"}
              </div>

              <div className="result-amount">
                {result === "loss"
                  ? `-$${betAmount.toFixed(2)}`
                  : `+$${payout.toFixed(2)}`}
              </div>
            </div>
          )}

          {/* ERROR */}

          {error && (
            <div className="game-error">
              <span>!</span>
              {error}
            </div>
          )}

          {/* NEW GAME */}

          <button
            className="new-game-button"
            onClick={initializeGame}
            disabled={playing}
          >
            New Game
          </button>

        </section>

        {/* HISTORY */}

        {/* <section className="history-section">

          <div className="section-heading">
            <div>
              <h2>Recent Rounds</h2>
              <p>
                Your latest Hi-Lo results
              </p>
            </div>

            <button
              onClick={refreshGame}
              disabled={playing}
              className="refresh-button"
            >
              ↻
            </button>
          </div>

          <RoundHistory rounds={rounds} />

        </section> */}

        <footer className="game-footer">
          Hi-Lo · Play responsibly
        </footer>

      </div>
    </main>
  );
}