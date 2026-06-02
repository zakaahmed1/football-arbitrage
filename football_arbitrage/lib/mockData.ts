import { ArbitrageOpportunity, League } from '../types';

export const leagues: League[] = [
  { id: 'premier', name: "Premier League", sport: 'Football' },
  { id: 'la_liga', name: "La Liga", sport: 'Football' },
  { id: 'champions', name: "Champions League", sport: 'Football' },
];

export const opportunities: ArbitrageOpportunity[] = [
  {
    id: 'arb1',
    homeTeam: 'West Hame',
    awayTeam: 'Brentford',
    startTime: new Date(Date.now() + 1000 * 60 * 60 * 4).toISOString(),
    sport: 'Football',
    leagueId: 'premier',
    profitPercent: 0.8,
    odds: [
      { bookmaker: 'Bet365', market: 'Under 1 Shots on Target', odds: 2/9 },
      { bookmaker: 'Betway', market: '1+ Shots on Target', odds: 19/4 },
    ],
  },
  {
    id: 'arb2',
    homeTeam: 'Real Madrid',
    awayTeam: 'Barcelona',
    startTime: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    sport: 'Football',
    leagueId: 'la_liga',
    profitPercent: 1.9,
    odds: [
      { bookmaker: 'BookC', market: '1X2', odds: 2.8 },
      { bookmaker: 'BookD', market: '1X2', odds: 2.9 },
    ],
  },
  {
    id: 'arb3',
    homeTeam: 'PSG',
    awayTeam: 'Bayern Munich',
    startTime: new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString(),
    sport: 'Football',
    leagueId: 'champions',
    profitPercent: 3.6,
    odds: [
      { bookmaker: 'BookE', market: '1X2', odds: 2.2 },
      { bookmaker: 'BookF', market: '1X2', odds: 3.5 },
    ],
  },
];

export default { leagues, opportunities };
