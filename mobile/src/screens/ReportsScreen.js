import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  TouchableOpacity, 
  ActivityIndicator, 
  Linking,
  Alert,
  RefreshControl 
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { reportAPI } from '../services/api';
import { THEME } from '../utils/theme';

export const ReportsScreen = ({ navigation }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchReports = async () => {
    try {
      const data = await reportAPI.list();
      setReports(data);
    } catch (err) {
      console.warn('Failed to load mobile reports:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchReports();
  };

  const handleDownload = (inspectionId, format = 'pdf') => {
    const url = reportAPI.getDownloadUrl(inspectionId, format);
    Linking.openURL(url).catch(() => {
      Alert.alert('Download Error', `Could not open ${format.toUpperCase()} file on device.`);
    });
  };

  const showFormatPicker = (inspectionId) => {
    Alert.alert(
      'Export Inspection Report',
      'Select report format to download:',
      [
        { text: 'PDF (Official Report)', onPress: () => handleDownload(inspectionId, 'pdf') },
        { text: 'Word (.docx Editable Draft)', onPress: () => handleDownload(inspectionId, 'docx') },
        { text: 'CSV (Audit Spreadsheet)', onPress: () => handleDownload(inspectionId, 'csv') },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  const renderItem = ({ item }) => {
    const isComp = item.compliance_status === 'COMPLIANT';
    const isNon = item.compliance_status === 'NON-COMPLIANT';
    const badgeColor = isComp ? THEME.colors.statusCompliant : (isNon ? THEME.colors.statusNonCompliant : THEME.colors.statusReview);

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={{ flex: 1 }}>
            <Text style={styles.repId}>#REP-2026-{item.report_id}</Text>
            <Text style={styles.productName} numberOfLines={1}>{item.product_name}</Text>
            <Text style={styles.dateText}>
              {new Date(item.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
            </Text>
          </View>
          <View style={styles.scoreContainer}>
            <Text style={[styles.scoreText, { color: badgeColor }]}>{item.compliance_score}%</Text>
            <Text style={[styles.statusText, { color: badgeColor }]}>{item.compliance_status}</Text>
          </View>
        </View>

        <View style={styles.btnRow}>
          <TouchableOpacity 
            style={styles.viewBtn}
            onPress={() => navigation.navigate('Result', { inspectionId: item.inspection_id })}
          >
            <Ionicons name="eye-outline" size={16} color={THEME.colors.textPrimary} />
            <Text style={styles.viewBtnText}>View Details</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.downloadBtn}
            onPress={() => showFormatPicker(item.inspection_id)}
          >
            <Ionicons name="download-outline" size={16} color="#FFFFFF" />
            <Text style={styles.downloadBtnText}>Export Report</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Statutory Reports Archive</Text>
        <Text style={styles.headerSubtitle}>Official Legal Metrology compliance PDF certificates</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={THEME.colors.accentLight} />
        </View>
      ) : (
        <FlatList
          data={reports}
          renderItem={renderItem}
          keyExtractor={(item) => item.report_id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#38BDF8" />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="folder-open-outline" size={38} color={THEME.colors.textMuted} />
              <Text style={styles.emptyTitle}>No Generated Reports</Text>
              <Text style={styles.emptySub}>Official PDF reports are automatically generated when product labels are inspected.</Text>
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
    paddingBottom: 16,
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
  listContent: {
    padding: 16,
    paddingBottom: 30,
  },
  card: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  repId: {
    fontSize: 10,
    fontWeight: '800',
    color: THEME.colors.accentLight,
    letterSpacing: 0.5,
  },
  productName: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
    marginTop: 2,
  },
  dateText: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  scoreContainer: {
    alignItems: 'flex-end',
  },
  scoreText: {
    fontSize: 18,
    fontWeight: '900',
  },
  statusText: {
    fontSize: 9,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  btnRow: {
    flexDirection: 'row',
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(30, 46, 78, 0.5)',
    paddingTop: 10,
  },
  viewBtn: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 8,
    borderRadius: THEME.radius.sm,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  viewBtnText: {
    color: THEME.colors.textPrimary,
    fontSize: 12,
    fontWeight: '600',
  },
  downloadBtn: {
    flex: 1,
    backgroundColor: THEME.colors.accentPrimary,
    paddingVertical: 8,
    borderRadius: THEME.radius.sm,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  downloadBtnText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  empty: {
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

export default ReportsScreen;
