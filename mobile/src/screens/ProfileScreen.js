import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  ActivityIndicator, 
  TextInput,
  Alert 
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { profileAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { THEME } from '../utils/theme';

export const ProfileScreen = () => {
  const { user: authUser, logout, setUser: setAuthUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  const [name, setName] = useState('');
  const [organization, setOrganization] = useState('');
  const [role, setRole] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await profileAPI.get();
        setProfile(data);
        setName(data.name || '');
        setOrganization(data.organization || '');
        setRole(data.role || '');
      } catch (err) {
        console.warn('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await profileAPI.update({ name, role, organization });
      setProfile((prev) => ({ ...prev, ...res.user }));
      setAuthUser(res.user);
      setEditing(false);
      Alert.alert('Success', 'Officer profile updated successfully.');
    } catch (err) {
      Alert.alert('Update Failed', err.response?.data?.detail || 'Could not update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to log out of SafeMetric?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log Out', style: 'destructive', onPress: logout }
    ]);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={THEME.colors.accentLight} />
      </View>
    );
  }

  const stats = profile?.stats || { total_inspections: 0, compliant: 0, non_compliant: 0, review_required: 0 };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Officer Profile</Text>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutIconBtn}>
          <Ionicons name="log-out-outline" size={22} color="#EF4444" />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Officer Card */}
        <View style={styles.avatarCard}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarInitial}>
              {profile?.name ? profile.name.charAt(0).toUpperCase() : 'O'}
            </Text>
          </View>
          <Text style={styles.profileName}>{profile?.name}</Text>
          <Text style={styles.profileRole}>{profile?.role}</Text>
          <Text style={styles.profileOrg}>{profile?.organization}</Text>
          <Text style={styles.profileEmail}>{profile?.email}</Text>
        </View>

        {/* Inspection Stats */}
        <Text style={styles.sectionHeader}>Enforcement Activity</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{stats.total_inspections}</Text>
            <Text style={styles.statTag}>TOTAL SCANS</Text>
          </View>
          <View style={[styles.statBox, { borderColor: THEME.colors.statusCompliantBorder }]}>
            <Text style={[styles.statNum, { color: THEME.colors.statusCompliant }]}>{stats.compliant}</Text>
            <Text style={styles.statTag}>COMPLIANT</Text>
          </View>
          <View style={[styles.statBox, { borderColor: THEME.colors.statusNonCompliantBorder }]}>
            <Text style={[styles.statNum, { color: THEME.colors.statusNonCompliant }]}>{stats.non_compliant}</Text>
            <Text style={styles.statTag}>NON-COMPLIANT</Text>
          </View>
          <View style={[styles.statBox, { borderColor: THEME.colors.statusReviewBorder }]}>
            <Text style={[styles.statNum, { color: THEME.colors.statusReview }]}>{stats.review_required}</Text>
            <Text style={styles.statTag}>REVIEW REQ.</Text>
          </View>
        </View>

        {/* Edit Profile Section */}
        <View style={styles.editSection}>
          <View style={styles.editHeader}>
            <Text style={styles.sectionHeader}>Officer Information</Text>
            <TouchableOpacity onPress={() => setEditing(!editing)}>
              <Text style={styles.editToggleText}>{editing ? 'Cancel' : 'Edit'}</Text>
            </TouchableOpacity>
          </View>

          {editing ? (
            <View style={styles.editCard}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Full Name</Text>
                <TextInput style={styles.input} value={name} onChangeText={setName} />
              </View>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Designation / Role</Text>
                <TextInput style={styles.input} value={role} onChangeText={setRole} />
              </View>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Organization / Zone</Text>
                <TextInput style={styles.input} value={organization} onChangeText={setOrganization} />
              </View>

              <TouchableOpacity style={styles.saveBtn} onPress={handleSave} disabled={saving}>
                {saving ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.saveBtnText}>Save Changes</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.infoCard}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Designation</Text>
                <Text style={styles.infoVal}>{profile?.role}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Department</Text>
                <Text style={styles.infoVal}>{profile?.organization}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Account Status</Text>
                <Text style={[styles.infoVal, { color: THEME.colors.statusCompliant }]}>Active & Authorized</Text>
              </View>
            </View>
          )}
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color="#EF4444" />
          <Text style={styles.logoutButtonText}>LOGOUT FROM SAFE METRIC</Text>
        </TouchableOpacity>
      </ScrollView>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  logoutIconBtn: {
    padding: 6,
  },
  scrollContent: {
    padding: 20,
  },
  avatarCard: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.lg,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    marginBottom: 20,
  },
  avatarCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: THEME.colors.accentPrimary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    elevation: 6,
  },
  avatarInitial: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFFFFF',
  },
  profileName: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  profileRole: {
    fontSize: 12,
    fontWeight: '700',
    color: THEME.colors.accentLight,
    marginTop: 2,
  },
  profileOrg: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
    marginTop: 2,
  },
  profileEmail: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 6,
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '800',
    color: THEME.colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  statBox: {
    flex: 1,
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  statNum: {
    fontSize: 18,
    fontWeight: '900',
    color: THEME.colors.textPrimary,
  },
  statTag: {
    fontSize: 8,
    fontWeight: '700',
    color: THEME.colors.textMuted,
    marginTop: 2,
  },
  editSection: {
    marginBottom: 24,
  },
  editHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  editToggleText: {
    fontSize: 12,
    fontWeight: '700',
    color: THEME.colors.accentLight,
  },
  infoCard: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(30, 46, 78, 0.5)',
  },
  infoLabel: {
    fontSize: 12,
    color: THEME.colors.textMuted,
  },
  infoVal: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME.colors.textPrimary,
  },
  editCard: {
    backgroundColor: THEME.colors.bgCard,
    borderRadius: THEME.radius.md,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  inputGroup: {
    marginBottom: 12,
  },
  inputLabel: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginBottom: 4,
  },
  input: {
    height: 42,
    backgroundColor: THEME.colors.bgDark,
    borderRadius: THEME.radius.sm,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    paddingHorizontal: 12,
    color: THEME.colors.textPrimary,
    fontSize: 13,
  },
  saveBtn: {
    backgroundColor: THEME.colors.accentPrimary,
    height: 44,
    borderRadius: THEME.radius.sm,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 6,
  },
  saveBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  logoutButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: THEME.radius.md,
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderWidth: 1,
    borderColor: THEME.colors.statusNonCompliantBorder,
    marginBottom: 30,
  },
  logoutButtonText: {
    color: '#EF4444',
    fontWeight: '800',
    fontSize: 13,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ProfileScreen;
