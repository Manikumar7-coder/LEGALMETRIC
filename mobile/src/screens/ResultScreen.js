import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  ActivityIndicator, 
  Linking,
  Alert 
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { inspectionAPI, reportAPI } from '../services/api';
import { THEME } from '../utils/theme';

export const ResultScreen = ({ route, navigation }) => {
  const { inspectionId } = route.params || {};
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadResult = async () => {
      if (!inspectionId) return;
      try {
        const data = await inspectionAPI.getById(inspectionId);
        setInspection(data);
      } catch (err) {
        Alert.alert('Error', 'Could not load inspection result.');
      } finally {
        setLoading(false);
      }
    };
    loadResult();
  }, [inspectionId]);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={THEME.colors.accentLight} />
        <Text style={styles.loadingText}>Retrieving Statutory Result...</Text>
      </View>
    );
  }

  if (!inspection) {
    return (
      <View style={styles.centerContainer}>
        <Text style={{ color: THEME.colors.textPrimary }}>Result Not Found</Text>
      </View>
    );
  }

  const isCompliant = inspection.compliance_status === 'COMPLIANT';
  const isNonCompliant = inspection.compliance_status === 'NON-COMPLIANT';
  const statusColor = isCompliant ? THEME.colors.statusCompliant : (isNonCompliant ? THEME.colors.statusNonCompliant : THEME.colors.statusReview);
  const statusBg = isCompliant ? THEME.colors.statusCompliantBg : (isNonCompliant ? THEME.colors.statusNonCompliantBg : THEME.colors.statusReviewBg);
  const statusBorder = isCompliant ? THEME.colors.statusCompliantBorder : (isNonCompliant ? THEME.colors.statusNonCompliantBorder : THEME.colors.statusReviewBorder);

  const violations = inspection.violations || [];
  const fields = inspection.fields || [];
  const ext = inspection.extracted_data || {};

  const handleDownload = (format = 'pdf') => {
    const url = reportAPI.getDownloadUrl(inspection.id, format);
    Linking.openURL(url).catch(() => {
      Alert.alert('Download Error', `Could not open ${format.toUpperCase()} file on device.`);
    });
  };

  const handleExportModal = () => {
    Alert.alert(
      'Export Inspection Report',
      'Select statutory report format:',
      [
        { text: 'PDF (Official Report)', onPress: () => handleDownload('pdf') },
        { text: 'Word (.docx Editable Draft)', onPress: () => handleDownload('docx') },
        { text: 'CSV (Audit Spreadsheet)', onPress: () => handleDownload('csv') },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={20} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Inspection Result</Text>
        <TouchableOpacity onPress={handleExportModal} style={styles.pdfIconBtn}>
          <Ionicons name="document-text" size={20} color={THEME.colors.accentLight} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Big Compliance Status Banner */}
        <View style={[styles.bannerCard, { backgroundColor: statusBg, borderColor: statusBorder }]}>
          <View style={styles.bannerHeader}>
            <Ionicons 
              name={isCompliant ? "checkmark-circle" : (isNonCompliant ? "close-circle" : "alert-circle")} 
              size={36} 
              color={statusColor} 
            />
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={[styles.bannerSub, { color: statusColor }]}>STATUTORY DETERMINATION</Text>
              <Text style={styles.bannerTitle}>{inspection.compliance_status}</Text>
            </View>
            <View style={styles.scorePill}>
              <Text style={[styles.scoreVal, { color: statusColor }]}>{inspection.compliance_score}%</Text>
              <Text style={styles.scoreLabel}>SCORE</Text>
            </View>
          </View>

          <Text style={styles.productNameText} numberOfLines={2}>
            {inspection.product_name}
          </Text>
          <Text style={styles.insRefText}>
            Ref: #INS-{inspection.id} • {new Date(inspection.inspection_date).toLocaleDateString('en-GB')}
          </Text>
        </View>

        {/* Action Buttons Strip */}
        <View style={styles.actionStrip}>
          <TouchableOpacity style={styles.primaryAction} onPress={handleExportModal}>
            <Ionicons name="download-outline" size={18} color="#FFFFFF" />
            <Text style={styles.primaryActionText}>Export Report (PDF / DOCX / CSV)</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryAction} onPress={() => navigation.navigate('Scan')}>
            <Ionicons name="scan-outline" size={18} color={THEME.colors.textPrimary} />
            <Text style={styles.secondaryActionText}>Scan Next</Text>
          </TouchableOpacity>
        </View>

        {/* Violations Section */}
        {violations.length > 0 && (
          <View style={styles.sectionBox}>
            <View style={styles.sectionHeader}>
              <Ionicons name="warning-outline" size={20} color="#EF4444" />
              <Text style={styles.sectionTitleRed}>Compliance Violations ({violations.length})</Text>
            </View>

            {violations.map((v, idx) => (
              <View key={idx} style={styles.violationCard}>
                <View style={styles.violationTop}>
                  <Text style={styles.violationField}>{v.field}</Text>
                  <View style={styles.sevBadge}>
                    <Text style={styles.sevText}>{v.severity}</Text>
                  </View>
                </View>
                <Text style={styles.violationIssue}>{v.issue}</Text>
                <Text style={styles.violationLaw}>Rule: {v.rule_reference}</Text>
                <Text style={styles.violationRec}>Advisory: {v.recommendation}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Extracted Declarations Card */}
        <View style={styles.sectionBox}>
          <View style={styles.sectionHeader}>
            <Ionicons name="list-outline" size={20} color={THEME.colors.accentLight} />
            <Text style={styles.sectionTitle}>Statutory Declarations Checklist</Text>
          </View>

          {fields.map((f, idx) => {
            const isFound = f.status === 'Found';
            const statColor = isFound ? THEME.colors.statusCompliant : (f.status === 'Low Confidence' ? THEME.colors.statusReview : THEME.colors.statusNonCompliant);
            const fontFld = inspection.font_analysis?.fields?.[f.field_name];
            return (
              <View key={idx} style={styles.declRow}>
                <View style={{ flex: 1, marginRight: 10 }}>
                  <Text style={styles.declField}>{f.field_name.replace(/_/g, ' ').toUpperCase()}</Text>
                  <Text style={styles.declValue} numberOfLines={2}>
                    {f.extracted_value || '— Not Detected —'}
                  </Text>
                  {fontFld?.char_height_mm && (
                    <Text style={{ fontSize: 10, color: fontFld.status === 'PASS' ? THEME.colors.statusCompliant : (fontFld.status === 'FAIL' ? THEME.colors.statusNonCompliant : THEME.colors.statusReview), marginTop: 3, fontWeight: '700' }}>
                      Font: {fontFld.char_height_mm} mm (min {fontFld.min_required_mm} mm) • {fontFld.status}
                    </Text>
                  )}
                </View>
                <View style={styles.declStatusBox}>
                  <Text style={[styles.declStatusText, { color: statColor }]}>{f.status}</Text>
                  {isFound && <Text style={styles.declConf}>{f.confidence}% OCR</Text>}
                </View>
              </View>
            );
          })}
        </View>

        {/* Font Size & Readability Analysis Section (Rule 7, PCR 2011) */}
        {inspection.font_analysis && (
          <View style={styles.sectionBox}>
            <View style={styles.sectionHeader}>
              <Ionicons name="text-outline" size={20} color={THEME.colors.accentLight} />
              <View style={{ flex: 1, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={styles.sectionTitle}>Font Size Analysis (Rule 7)</Text>
                <View style={[styles.sevBadge, {
                  backgroundColor: inspection.font_analysis.overall_status === 'PASS'
                    ? THEME.colors.statusCompliantBg
                    : (inspection.font_analysis.overall_status === 'FAIL' ? THEME.colors.statusNonCompliantBg : THEME.colors.statusReviewBg)
                }]}>
                  <Text style={[styles.sevText, {
                    color: inspection.font_analysis.overall_status === 'PASS'
                      ? THEME.colors.statusCompliant
                      : (inspection.font_analysis.overall_status === 'FAIL' ? THEME.colors.statusNonCompliant : THEME.colors.statusReview)
                  }]}>
                    {inspection.font_analysis.overall_status}
                  </Text>
                </View>
              </View>
            </View>

            {Object.entries(inspection.font_analysis.fields || {}).map(([key, fld]) => {
              const isP = fld.status === 'PASS';
              const isF = fld.status === 'FAIL';
              const col = isP ? THEME.colors.statusCompliant : (isF ? THEME.colors.statusNonCompliant : THEME.colors.statusReview);
              return (
                <View key={key} style={[styles.declRow, { paddingVertical: 8 }]}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.declField}>{fld.field_label}</Text>
                    <Text style={{ fontSize: 13, fontWeight: '700', color: col, marginTop: 2 }}>
                      {fld.char_height_mm ? `${fld.char_height_mm} mm` : 'N/A'}
                    </Text>
                    <Text style={{ fontSize: 10, color: THEME.colors.textMuted }}>
                      min required: {fld.min_required_mm || 1.0} mm
                    </Text>
                  </View>
                  <View style={styles.declStatusBox}>
                    <Text style={[styles.declStatusText, { color: col }]}>{fld.status}</Text>
                    <Text style={styles.declConf}>
                      {inspection.font_analysis.estimation_method === 'user_calibrated_package_dimensions' ? 'Calibrated' : 'Heuristic'}
                    </Text>
                  </View>
                </View>
              );
            })}

            {inspection.font_analysis.limitations && (
              <Text style={{ fontSize: 10, color: THEME.colors.textMuted, marginTop: 8, fontStyle: 'italic' }}>
                {inspection.font_analysis.limitations}
              </Text>
            )}
          </View>
        )}

        {/* Declaration Placement & Grouping Card (Rule 8) */}
        {inspection.placement_analysis && (
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <View>
                <Text style={styles.cardTitle}>Placement & Grouping</Text>
                <Text style={styles.cardSubtitle}>Rule 8(1) & 8(2) Compliance Check</Text>
              </View>
              <View style={[
                styles.badge,
                {
                  backgroundColor: inspection.placement_analysis.status === 'PASS'
                    ? THEME.colors.statusCompliantBg
                    : (inspection.placement_analysis.status === 'FAIL' ? THEME.colors.statusNonCompliantBg : THEME.colors.statusReviewBg)
                }
              ]}>
                <Text style={[
                  styles.badgeText,
                  {
                    color: inspection.placement_analysis.status === 'PASS'
                      ? THEME.colors.statusCompliant
                      : (inspection.placement_analysis.status === 'FAIL' ? THEME.colors.statusNonCompliant : THEME.colors.statusReview)
                  }
                ]}>
                  {inspection.placement_analysis.status}
                </Text>
              </View>
            </View>

            {/* Grouping detail */}
            <View style={{ marginTop: 10, padding: 10, backgroundColor: THEME.colors.surface, borderRadius: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ fontSize: 13, fontWeight: '700', color: THEME.colors.textPrimary }}>
                  PDP Grouping
                </Text>
                <Text style={{
                  fontSize: 11,
                  fontWeight: '700',
                  color: inspection.placement_analysis.grouping?.status === 'PASS'
                    ? THEME.colors.statusCompliant
                    : (inspection.placement_analysis.grouping?.status === 'FAIL' ? THEME.colors.statusNonCompliant : THEME.colors.statusReview)
                }}>
                  {inspection.placement_analysis.grouping?.status || 'NEEDS_REVIEW'}
                </Text>
              </View>
              <Text style={{ fontSize: 11, color: THEME.colors.textSecondary }}>
                {inspection.placement_analysis.grouping?.explanation}
              </Text>
            </View>

            {/* Clear space detail */}
            <View style={{ marginTop: 8, padding: 10, backgroundColor: THEME.colors.surface, borderRadius: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ fontSize: 13, fontWeight: '700', color: THEME.colors.textPrimary }}>
                  Net Qty Clear Space
                </Text>
                <Text style={{
                  fontSize: 11,
                  fontWeight: '700',
                  color: inspection.placement_analysis.clear_space?.status === 'PASS'
                    ? THEME.colors.statusCompliant
                    : (inspection.placement_analysis.clear_space?.status === 'FAIL' ? THEME.colors.statusNonCompliant : THEME.colors.statusReview)
                }}>
                  {inspection.placement_analysis.clear_space?.status || 'NEEDS_REVIEW'}
                </Text>
              </View>
              <Text style={{ fontSize: 11, color: THEME.colors.textSecondary }}>
                {inspection.placement_analysis.clear_space?.explanation}
              </Text>
            </View>
          </View>
        )}

        {/* Mandatory Regulatory Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Ionicons name="information-circle-outline" size={18} color={THEME.colors.textMuted} style={{ marginTop: 2 }} />
          <Text style={styles.disclaimerText}>
            SafeMetric verifies packaged product label declarations under the Legal Metrology (Packaged Commodities) Rules, 2011. Automated compliance assistance only; final regulatory determination remains subject to designated officer inspection.
          </Text>
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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: THEME.colors.bgMain,
    gap: 12,
  },
  loadingText: {
    color: THEME.colors.textSecondary,
    fontSize: 13,
  },
  header: {
    paddingTop: 48,
    paddingHorizontal: 20,
    paddingBottom: 14,
    backgroundColor: THEME.colors.bgDark,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.borderSubtle,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    padding: 6,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  pdfIconBtn: {
    padding: 6,
  },
  scrollContent: {
    padding: 18,
  },
  bannerCard: {
    borderRadius: THEME.radius.lg,
    padding: 20,
    borderWidth: 2,
    marginBottom: 16,
  },
  bannerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  bannerSub: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  bannerTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: THEME.colors.textPrimary,
  },
  scorePill: {
    backgroundColor: '#070D19',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: THEME.radius.md,
    alignItems: 'center',
  },
  scoreVal: {
    fontSize: 18,
    fontWeight: '900',
  },
  scoreLabel: {
    fontSize: 8,
    color: THEME.colors.textMuted,
    fontWeight: '700',
  },
  productNameText: {
    fontSize: 15,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
    marginTop: 14,
  },
  insRefText: {
    fontSize: 11,
    color: THEME.colors.textSecondary,
    marginTop: 4,
  },
  actionStrip: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  primaryAction: {
    flex: 1.4,
    backgroundColor: THEME.colors.accentPrimary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: THEME.radius.md,
  },
  primaryActionText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  secondaryAction: {
    flex: 1,
    backgroundColor: '#1E293B',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: THEME.radius.md,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  secondaryActionText: {
    color: THEME.colors.textPrimary,
    fontWeight: '600',
    fontSize: 13,
  },
  sectionBox: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.lg,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  sectionTitleRed: {
    fontSize: 14,
    fontWeight: '800',
    color: '#EF4444',
  },
  violationCard: {
    backgroundColor: '#070D19',
    borderRadius: THEME.radius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    marginBottom: 10,
  },
  violationTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  violationField: {
    fontSize: 11,
    fontWeight: '800',
    color: '#EF4444',
    textTransform: 'uppercase',
  },
  sevBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  sevText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#EF4444',
  },
  violationIssue: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.colors.textPrimary,
    marginBottom: 4,
  },
  violationLaw: {
    fontSize: 11,
    color: THEME.colors.accentLight,
  },
  violationRec: {
    fontSize: 11,
    color: THEME.colors.textSecondary,
    marginTop: 2,
  },
  declRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(30, 46, 78, 0.6)',
  },
  declField: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.colors.textMuted,
  },
  declValue: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.colors.textPrimary,
    marginTop: 2,
  },
  declStatusBox: {
    alignItems: 'flex-end',
  },
  declStatusText: {
    fontSize: 11,
    fontWeight: '800',
  },
  declConf: {
    fontSize: 9,
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  disclaimerCard: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: '#070D19',
    borderRadius: THEME.radius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 20,
  },
  disclaimerText: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    lineHeight: 16,
    flex: 1,
  },
});

export default ResultScreen;
