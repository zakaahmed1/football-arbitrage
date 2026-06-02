export type Sport = 'Football';

export type League = {
  id: string;
  name: string;
  sport: Sport;
};

export type BookmakerOdds = {
  bookmaker: string;
  market: string;
  odds: number; // decimal odds
};

export type ArbitrageOpportunity = {
  id: string;
  homeTeam: string;
  awayTeam: string;
  startTime: string; // ISO
  sport: Sport;
  leagueId: string;
  profitPercent: number;
  odds: BookmakerOdds[];
};

