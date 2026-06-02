import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import OpportunityCard from '../components/OpportunityCard';
import { opportunities as mockOpportunities } from '../lib/mockData';
import { colors, spacing, typeSizes } from '../lib/theme';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <SafeAreaView edges={['top']} style={styles.safeArea}>
        <View style={styles.header}>
          <Text style={styles.title}>Arbitrage Opportunities</Text>
          <Text style={styles.subtitle}>Find profitable betting mismatches across bookmakers</Text>
        </View>

        <FlatList
          data={mockOpportunities}
          keyExtractor={(i) => i.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => <OpportunityCard item={item} />}
          ListEmptyComponent={() => (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No football arbitrage opportunities available.</Text>
            </View>
          )}
        />
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  safeArea: { flex: 1 },
  header: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, paddingBottom: spacing.sm },
  title: { fontSize: typeSizes.h1, fontWeight: '800', color: '#0B1F1A' },
  subtitle: { color: colors.muted, marginTop: 6 },
  list: { paddingHorizontal: spacing.md, paddingBottom: spacing.lg, paddingTop: spacing.sm },
  empty: { marginTop: 32, alignItems: 'center' },
  emptyText: { color: colors.muted },
});
