export type Prediction = "higher" | "lower";

export type RoundResult = "win" | "loss" | "push";

export type GameStatus = "active" | "completed";

export interface Card {
  rank: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  value: number;
}

export interface StartGameResponse {
  game_id: string;
  status: GameStatus;
  current_card: Card;
  balance: string;
}

export interface GameState {
  player_id: string;
  status: GameStatus;
  current_card: Card;
  balance: string;
  current_round_id: string | null;
  round_number: number;
  updated_at: string;
  game_id: string;
}

export interface PlayRoundRequest {
  bet_amount: number;
  prediction: Prediction;
}

export interface PlayRoundResponse {
  game_id: string;
  round_id: string;
  previous_card: Card;
  next_card: Card;
  prediction: Prediction;
  result: RoundResult;
  bet_amount: number;
  payout: number;
  balance: number;
}

export interface Round {
  game_id: string;
  player_id: string;
  round_number: number;
  bet_amount: number;
  prediction: Prediction;
  previous_card: Card;
  next_card: Card;
  result: RoundResult;
  payout: number;
  status: string;
  round_id: string;
}

export interface RoundHistoryResponse {
  player_id: string;
  rounds: Round[];
  total: number;
}

export interface GameRoundsResponse {
  game_id: string;
  rounds: Round[];
  total: number;
}