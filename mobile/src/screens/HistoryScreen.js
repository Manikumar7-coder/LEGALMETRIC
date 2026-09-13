import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator,
  RefreshControl 
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { inspectionAPI } from '../services/api';
import { THEME } from '../utils/theme';

export const HistoryScreen = ({ navigation }) => {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const fetchHistory = async () => {
    try {
      const data = await inspectionAPI.list({
        status: statusFilter,
        search: search || undefined,
      });
      setInspections(data);
    } catch (err) {
      console.warn('Failed to load mobile history:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [statusFilter]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchHistory();
  };

  const renderItem = ({ item }) => {
    const isComp = item.compliance_status === 'COMPLIANT';
    const isNon = item.compliance_status === 'NON-COMPLIANT';
    const badgeColor = isComp ? THEME.colors.statusCompliant : (isNon ? THEME.colors.statusNonCompliant : THEME.colors.statusReview);
    const badgeBg = isComp ? THEME.colors.statusCompliantBg : (isNon ? THEME.colors.statusNonCompliantBg : THEME.colors.statusReviewBg);

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('Result', { inspectionId: item.id })}
      >
        <View style={styles.cardHeader}>
          <View style={{ flex: 1, marginRight: 8 }}>
            <Text style={styles.productName} numberOfLines={1}>{item.product_name}</Text>
            <Text style={styles.insIdText}>#INS-{item.id} • {new Date(item.inspection_date).toLocaleDateString('en-GB')}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: badgeBg }]}>
            <Text style={[styles.badgeText, { color: badgeColor }]}>{item.compliance_status}</Text>
          </View>
        </View>

        <View style={styles.cardFooter}>
          <Text style={styles.scoreText}>Compliance Score: <Text style={{ color: badgeColor, fontWeight: '800' }}>{item.compliance_score}%</Text></Text>
          <View style={styles.viewRow}>
            <Text style={styles.viewText}>View Report</Text>
            <Ionicons name="chevron-forward" size={14} color={THEME.colors.accentLight} />
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Inspection Audit History</Text>
        <Text style={styles.headerSubtitle}>Logged field compliance verification records</Text>

        {/* Search */}
        <View style={styles.searchWrapper}>
          <Ionicons name="search" size={16} color={THEME.colors.textMuted} style={{ marginRight: 8 }} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search commodity name..."
            placeholderTextColor={THEME.colors.textMuted}
            value={search}
            onChangeText={setSearch}
            onSubmitEditing={fetchHistory}
          />
        </View>

        {/* Filter Pills */}
        <View style={styles.pillRow}>
          {['ALL', 'COMPLIANT', 'NON-COMPLIANT', 'REVIEW REQUIRED'].map((st) => (
            <TouchableOpacity
              key={st}
              style={[styles.filterPill, statusFilter === st && styles.filterPillActive]}
              onPress={() => setStatusFilter(st)}
            >
              <Text style={[styles.filterPillText, statusFilter === st && styles.filterPillTextActive]}>
                {st}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* List */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={THEME.colors.accentLight} />
        </View>
      ) : (
        <FlatList
          data={inspections}
          renderItem={renderItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#38BDF8" />}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="documents-outline" size={40} color={THEME.colors.textMuted} />
              <Text style={styles.emptyTitle}>No matching inspections</Text>
              <Text style={styles.emptySub}>Capture a product label in the Scan tab to record inspections.</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.bgMain,
  },
  header: {
    paddingTop: 48,
    paddingHorizontal: 20,
    paddingBottom: 14,
    backgroundColor: THEME.colors.bgDark,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.borderSubtle,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  searchWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F1D36',
    borderRadius: THEME.radius.md,
    paddingHorizontal: 12,
    height: 40,
    marginTop: 12,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  searchInput: {
    flex: 1,
    color: THEME.colors.textPrimary,
    fontSize: 13,
  },
  pillRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 12,
    flexWrap: 'wrap',
  },
  filterPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: THEME.radius.round,
    backgroundColor: '#0F1D36',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  filterPillActive: {
    backgroundColor: 'rgba(37, 99, 235, 0.25)',
    borderColor: THEME.colors.accentPrimary,
  },
  filterPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.textMuted,
  },
  filterPillTextActive: {
    color: '#FFFFFF',
  },
  listContent: {
    padding: 16,
    paddingBottom: 30,
  },
  card: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  productName: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
  },
  insIdText: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: THEME.radius.round,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: 'rgba(30, 46, 78, 0.5)',
    paddingTop: 8,
  },
  scoreText: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
  },
  viewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  viewText: {
    fontSize: 11,
    fontWeight: '600',
    color: THEME.colors.accentLight,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
    marginTop: 10,
  },
  emptySub: {
    fontSize: 12,
    color: THEME.colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
  },
});

export default HistoryScreen;
