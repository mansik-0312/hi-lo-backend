"use client";

import { useState } from "react";

import {
  playHiLoRound,
  startHiLoGame,
} from "@/lib/api/hilo";

import {
  GameState,
  PlayRoundResponse,
  Prediction,
} from "@/types/hilo";

export function useHiLoGame() {
  const [game, setGame] =
    useState<GameState | null>(null);

  const [lastRound, setLastRound] =
    useState<PlayRoundResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function startGame(
    initialBalance: number,
  ) {
    try {
      setLoading(true);
      setError(null);
      setLastRound(null);

      const response =
        await startHiLoGame({
          initial_balance: initialBalance,
        });

      setGame({
        game_id: response.game_id,
        player_id: "demo-player",
        status: response.status,
        current_card: response.current_card,
        balance: response.balance,
        round_number: 0,
        updated_at: new Date().toISOString(),
      });

      return response;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to start game.";

      setError(message);

      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function playRound(
    betAmount: number,
    prediction: Prediction,
  ) {
    if (!game) {
      setError("No active game.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response =
        await playHiLoRound(
          game.game_id,
          {
            bet_amount: betAmount,
            prediction,
          },
        );

      setLastRound(response);

      setGame((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          current_card: response.next_card,
          balance: String(
            response.balance,
          ),
          current_round_id:
            response.round_id,
          round_number:
            current.round_number + 1,
        };
      });

      return response;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to play round.";

      setError(message);

      throw err;
    } finally {
      setLoading(false);
    }
  }

  function clearError() {
    setError(null);
  }

  return {
    game,
    lastRound,
    loading,
    error,
    startGame,
    playRound,
    clearError,
  };
}