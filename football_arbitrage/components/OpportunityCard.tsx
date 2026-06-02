import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ArbitrageOpportunity } from '../types';
import { leagues } from '../lib/mockData';
import { colors, spacing, typeSizes, radii } from '../lib/theme';

type Props = {
  item: ArbitrageOpportunity;
};

export default function OpportunityCard({ item }: Props) {
  const topOdds = item.odds.slice(0, 2).map((o) => `${o.bookmaker}: ${o.odds}`).join(' | ');
  const leagueName = leagues.find((league) => league.id === item.leagueId)?.name ?? item.leagueId;

  const start = new Date(item.startTime);
  const timeString = start.toLocaleString();

  return (
    <View style={styles.card}>
      <View style={styles.rowTop}>
        <View>
          <Text style={styles.matchup}>{item.homeTeam} vs {item.awayTeam}</Text>
          <Text style={styles.league}>{leagueName}</Text>
        </View>
        <View style={styles.rightCol}>
          <Text style={styles.profit}>{item.profitPercent.toFixed(2)}%</Text>
        </View>
      </View>

      <View style={styles.rowBottom}>
        <Text style={styles.time}>{timeString}</Text>
        <Text style={styles.odds}>{topOdds}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  rowTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  matchup: {
    fontSize: typeSizes.h2,
    fontWeight: '700',
    marginBottom: 4,
  },
  league: {
    fontSize: typeSizes.small,
    color: colors.muted,
  },
  rightCol: {
    alignItems: 'flex-end',
  },
  profit: {
    color: colors.primary,
    fontWeight: '700',
    fontSize: 16,
  },
  rowBottom: {
    marginTop: spacing.sm,
  },
  time: {
    fontSize: typeSizes.small,
    color: colors.muted,
    marginBottom: 6,
  },
  odds: {
    fontSize: typeSizes.body,
    color: colors.muted,
  },
});
