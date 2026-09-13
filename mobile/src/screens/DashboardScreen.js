import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  RefreshControl,
  Image,
  ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { dashboardAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { THEME } from '../utils/theme';

export const DashboardScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await dashboardAPI.getStats();
      setStats(data);
    } catch (err) {
      console.warn('Failed to load mobile dashboard stats:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  const total = stats?.total_inspections || 0;
  const compliant = stats?.compliant_count || 0;
  const nonCompliant = stats?.non_compliant_count || 0;
  const recent = stats?.recent_inspections || [];

  return (
    <View style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#38BDF8" />}
      >
        {/* Top Field Officer Greeting */}
        <View style={styles.headerBar}>
          <View>
            <Text style={styles.appName}>SAFE METRIC</Text>
            <Text style={styles.greeting}>Good day, {user?.name ? user.name.split(' ')[0] : 'Officer'}</Text>
          </View>
          <View style={styles.onlineBadge}>
            <View style={styles.onlineDot} />
            <Text style={styles.onlineText}>PCR 2011 Active</Text>
          </View>
        </View>

        {/* Large Primary Action Hero Card: SCAN PRODUCT */}
        <View style={styles.heroCard}>
          <View style={styles.heroHeader}>
            <View style={styles.heroIconBadge}>
              <Ionicons name="scan" size={24} color="#FFFFFF" />
            </View>
            <View>
              <Text style={styles.heroTitle}>FIELD INSPECTION</Text>
              <Text style={styles.heroSubtitle}>Capture & Verify Commodity Label</Text>
            </View>
          </View>

          <Text style={styles.heroDesc}>
            Instant optical character extraction and statutory Legal Metrology rule validation.
          </Text>

          {/* Two Primary Action Buttons */}
          <View style={styles.heroActions}>
            <TouchableOpacity 
              style={styles.cameraButton}
              onPress={() => navigation.navigate('Scan', { mode: 'camera' })}
            >
              <Ionicons name="camera" size={20} color="#FFFFFF" />
              <Text style={styles.cameraButtonText}>Scan with Camera</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.galleryButton}
              onPress={() => navigation.navigate('Scan', { mode: 'gallery' })}
            >
              <Ionicons name="images-outline" size={18} color={THEME.colors.textPrimary} />
              <Text style={styles.galleryButtonText}>Upload Image</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Quick Statistics Strip */}
        <View style={styles.statsStrip}>
          <View style={styles.statBox}>
            <Text style={styles.statVal}>{total}</Text>
            <Text style={styles.statLabel}>INSPECTIONS</Text>
          </View>
          <View style={[styles.statBox, { borderColor: THEME.colors.statusCompliantBorder }]}>
            <Text style={[styles.statVal, { color: THEME.colors.statusCompliant }]}>{compliant}</Text>
            <Text style={styles.statLabel}>COMPLIANT</Text>
          </View>
          <View style={[styles.statBox, { borderColor: THEME.colors.statusNonCompliantBorder }]}>
            <Text style={[styles.statVal, { color: THEME.colors.statusNonCompliant }]}>{nonCompliant}</Text>
            <Text style={styles.statLabel}>VIOLATIONS</Text>
          </View>
        </View>

        {/* Recent Inspections Section */}
        <View style={styles.recentSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Field Inspections</Text>
            <TouchableOpacity onPress={() => navigation.navigate('History')}>
              <Text style={styles.seeAllText}>View All</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <ActivityIndicator color={THEME.colors.accentLight} style={{ marginVertical: 20 }} />
          ) : recent.length > 0 ? (
            recent.map((item) => {
              const isComp = item.compliance_status === 'COMPLIANT';
              const isNon = item.compliance_status === 'NON-COMPLIANT';
              const badgeColor = isComp ? THEME.colors.statusCompliant : (isNon ? THEME.colors.statusNonCompliant : THEME.colors.statusReview);
              const badgeBg = isComp ? THEME.colors.statusCompliantBg : (isNon ? THEME.colors.statusNonCompliantBg : THEME.colors.statusReviewBg);

              return (
                <TouchableOpacity
                  key={item.id}
                  style={styles.recentCard}
                  onPress={() => navigation.navigate('Result', { inspectionId: item.id })}
                >
                  <View style={styles.recentInfo}>
                    <Text style={styles.recentName} numberOfLines={1}>
                      {item.product_name}
                    </Text>
                    <Text style={styles.recentDate}>
                      ID: #INS-{item.id} • {new Date(item.inspection_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                    </Text>
                  </View>

                  <View style={[styles.statusBadge, { backgroundColor: badgeBg }]}>
                    <Text style={[styles.statusText, { color: badgeColor }]}>
                      {item.compliance_status}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="document-text-outline" size={32} color={THEME.colors.textMuted} />
              <Text style={styles.emptyText}>No field inspections recorded yet</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.bgMain,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 48,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  appName: {
    fontSize: 12,
    fontWeight: '900',
    color: THEME.colors.accentLight,
    letterSpacing: 1.5,
  },
  greeting: {
    fontSize: 20,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
    marginTop: 2,
  },
  onlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: THEME.radius.round,
    borderWidth: 1,
    borderColor: THEME.colors.statusCompliantBorder,
  },
  onlineDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: THEME.colors.statusCompliant,
  },
  onlineText: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.statusCompliant,
  },
  heroCard: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.xl,
    padding: 22,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.35)',
    shadowColor: THEME.colors.accentPrimary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 14,
    elevation: 8,
    marginBottom: 20,
  },
  heroHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 10,
  },
  heroIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: THEME.colors.accentPrimary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: THEME.colors.accentLight,
    letterSpacing: 0.8,
  },
  heroSubtitle: {
    fontSize: 16,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  heroDesc: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
    lineHeight: 18,
    marginBottom: 16,
  },
  heroActions: {
    flexDirection: 'row',
    gap: 10,
  },
  cameraButton: {
    flex: 1.2,
    backgroundColor: THEME.colors.accentPrimary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: THEME.radius.md,
    elevation: 3,
  },
  cameraButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  galleryButton: {
    flex: 1,
    backgroundColor: '#1E293B',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 14,
    borderRadius: THEME.radius.md,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  galleryButtonText: {
    color: THEME.colors.textPrimary,
    fontWeight: '600',
    fontSize: 13,
  },
  statsStrip: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 24,
  },
  statBox: {
    flex: 1,
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    alignItems: 'center',
  },
  statVal: {
    fontSize: 18,
    fontWeight: '900',
    color: THEME.colors.textPrimary,
  },
  statLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: THEME.colors.textMuted,
    marginTop: 2,
    letterSpacing: 0.5,
  },
  recentSection: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  seeAllText: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME.colors.accentLight,
  },
  recentCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 8,
  },
  recentInfo: {
    flex: 1,
    marginRight: 10,
  },
  recentName: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
  },
  recentDate: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: THEME.radius.round,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  emptyCard: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 30,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  emptyText: {
    fontSize: 12,
    color: THEME.colors.textMuted,
    marginTop: 8,
  },
});

export default DashboardScreen;
