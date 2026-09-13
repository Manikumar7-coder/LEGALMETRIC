import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  Image, 
  ActivityIndicator, 
  Alert,
  ScrollView,
  Platform
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { inspectionAPI } from '../services/api';
import { THEME } from '../utils/theme';

export const ScanScreen = ({ route, navigation }) => {
  const [permission, requestPermission] = useCameraPermissions();
  const [photoUri, setPhotoUri] = useState(null);
  const [demoSample, setDemoSample] = useState(null);
  const [productName, setProductName] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState('');
  const cameraRef = useRef(null);

  // Check if initial mode passed from Dashboard
  useEffect(() => {
    if (route.params?.mode === 'gallery') {
      pickFromGallery();
    }
  }, [route.params]);

  const takePicture = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({ quality: 0.85 });
        if (photo?.uri) {
          setPhotoUri(photo.uri);
          setDemoSample(null);
        }
      } catch (err) {
        Alert.alert('Camera Error', 'Could not capture photo. Please try again or choose from gallery.');
      }
    }
  };

  const pickFromGallery = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: false,
      quality: 0.85,
    });

    if (!result.canceled && result.assets[0]?.uri) {
      setPhotoUri(result.assets[0].uri);
      setDemoSample(null);
    }
  };

  const handleSelectDemo = (demoType, name) => {
    setDemoSample(demoType);
    setPhotoUri(null);
    setProductName(name);
  };

  const handleRetake = () => {
    setPhotoUri(null);
    setDemoSample(null);
  };

  const handleAnalyze = async () => {
    if (!photoUri && !demoSample) {
      Alert.alert('No Image', 'Please capture a label photo or select a commodity.');
      return;
    }

    setAnalyzing(true);
    setAnalysisStep('Reading package label...');

    setTimeout(() => setAnalysisStep('Extracting declarations with OCR...'), 600);
    setTimeout(() => setAnalysisStep('Evaluating Legal Metrology rules...'), 1200);

    try {
      const formData = new FormData();
      if (photoUri) {
        const filename = photoUri.split('/').pop() || 'mobile_scan.jpg';
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : 'image/jpeg';
        formData.append('file', {
          uri: Platform.OS === 'android' ? photoUri : photoUri.replace('file://', ''),
          name: filename,
          type: type,
        });
      }
      if (demoSample) {
        formData.append('demo_sample', demoSample);
      }
      if (productName) {
        formData.append('product_name', productName);
      }

      const result = await inspectionAPI.analyze(formData);
      setAnalyzing(false);
      navigation.navigate('Result', { inspectionId: result.id });
    } catch (err) {
      setAnalyzing(false);
      Alert.alert(
        'Inspection Failed',
        err.response?.data?.detail || 'Unable to analyze package. Please check image clarity and connectivity.'
      );
    }
  };

  // If currently analyzing, show full-screen animated processing tracker
  if (analyzing) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.analyzingCard}>
          <ActivityIndicator size="large" color={THEME.colors.accentLight} style={{ marginBottom: 16 }} />
          <Text style={styles.analyzingTitle}>AI Regulatory Compliance</Text>
          <Text style={styles.analyzingStep}>{analysisStep}</Text>
          <Text style={styles.analyzingSub}>Checking declarations against PCR, 2011</Text>
        </View>
      </View>
    );
  }

  // Permission check
  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Ionicons name="camera-outline" size={48} color={THEME.colors.accentLight} style={{ marginBottom: 16 }} />
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionDesc}>
          SafeMetric requires camera permissions to capture and inspect commodity declarations.
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Grant Camera Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.galleryButton, { marginTop: 14 }]} onPress={pickFromGallery}>
          <Ionicons name="images-outline" size={18} color="#FFFFFF" />
          <Text style={styles.galleryButtonText}>Choose from Gallery</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <Text style={styles.topTitle}>SAFE METRIC</Text>
        <Text style={styles.topSubtitle}>Scan Packaged Commodity</Text>
      </View>

      {/* Main View: Camera Viewfinder OR Captured Preview */}
      {!photoUri && !demoSample ? (
        <View style={styles.cameraFrame}>
          <CameraView ref={cameraRef} style={styles.cameraView} facing="back">
            {/* Viewfinder Target Frame */}
            <View style={styles.overlayFrame}>
              <View style={styles.frameCornerTopLeft} />
              <View style={styles.frameCornerTopRight} />
              <View style={styles.frameCornerBottomLeft} />
              <View style={styles.frameCornerBottomRight} />
              <View style={styles.frameTag}>
                <Text style={styles.frameTagText}>ALIGN PRODUCT LABEL INSIDE FRAME</Text>
              </View>
            </View>

            {/* Bottom Camera Controls Bar */}
            <View style={styles.cameraControlBar}>
              <TouchableOpacity style={styles.galleryIconBtn} onPress={pickFromGallery}>
                <Ionicons name="images-outline" size={24} color="#FFFFFF" />
              </TouchableOpacity>

              <TouchableOpacity style={styles.shutterButton} onPress={takePicture}>
                <View style={styles.shutterInner} />
              </TouchableOpacity>

              <View style={{ width: 44 }} />
            </View>
          </CameraView>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.previewContainer}>
          <View style={styles.previewImageWrapper}>
            {photoUri ? (
              <Image source={{ uri: photoUri }} style={styles.previewImage} resizeMode="contain" />
            ) : (
              <View style={styles.demoPlaceholder}>
                <Ionicons name="cube-outline" size={48} color="#38BDF8" />
                <Text style={styles.demoPlaceholderTitle}>{productName}</Text>
                <Text style={styles.demoPlaceholderSub}>Demo Commodity Dataset Selected</Text>
              </View>
            )}
          </View>

          {/* Action Buttons */}
          <View style={styles.previewActions}>
            <TouchableOpacity style={styles.retakeBtn} onPress={handleRetake}>
              <Ionicons name="refresh" size={18} color="#FFFFFF" />
              <Text style={styles.retakeBtnText}>Retake / Change</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.analyzeBtn} onPress={handleAnalyze}>
              <Ionicons name="scan" size={20} color="#FFFFFF" />
              <Text style={styles.analyzeBtnText}>ANALYZE PRODUCT</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      )}

      {/* SIH Demo Benchmarks Quick Bar */}
      <View style={styles.demoBar}>
        <Text style={styles.demoBarTitle}>SIH DEMO SAMPLES:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.demoScroll}>
          <TouchableOpacity 
            style={[styles.demoPill, demoSample === 'saferice' && styles.demoPillActive]}
            onPress={() => handleSelectDemo('saferice', 'SafeRice Premium')}
          >
            <Text style={[styles.demoPillText, { color: '#10B981' }]}>✓ SafeRice (Compliant)</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.demoPill, demoSample === 'wafer' && styles.demoPillActive]}
            onPress={() => handleSelectDemo('wafer', 'Crispy Delight Wafers')}
          >
            <Text style={[styles.demoPillText, { color: '#EF4444' }]}>✕ Crispy Wafers (Violations)</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.demoPill, demoSample === 'oil' && styles.demoPillActive]}
            onPress={() => handleSelectDemo('oil', 'Olive Oil')}
          >
            <Text style={[styles.demoPillText, { color: '#F59E0B' }]}>⚠ Olive Oil (Review)</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.bgMain,
  },
  topHeader: {
    paddingTop: 46,
    paddingHorizontal: 20,
    paddingBottom: 12,
    backgroundColor: THEME.colors.bgDark,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.borderSubtle,
  },
  topTitle: {
    fontSize: 11,
    fontWeight: '900',
    color: THEME.colors.accentLight,
    letterSpacing: 1.2,
  },
  topSubtitle: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  cameraFrame: {
    flex: 1,
  },
  cameraView: {
    flex: 1,
    justifyContent: 'space-between',
  },
  overlayFrame: {
    flex: 1,
    margin: 30,
    marginTop: 40,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.4)',
    borderRadius: 16,
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: 16,
    position: 'relative',
  },
  frameCornerTopLeft: {
    position: 'absolute',
    top: -2,
    left: -2,
    width: 24,
    height: 24,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#38BDF8',
  },
  frameCornerTopRight: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 24,
    height: 24,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderColor: '#38BDF8',
  },
  frameCornerBottomLeft: {
    position: 'absolute',
    bottom: -2,
    left: -2,
    width: 24,
    height: 24,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#38BDF8',
  },
  frameCornerBottomRight: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 24,
    height: 24,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderColor: '#38BDF8',
  },
  frameTag: {
    backgroundColor: 'rgba(11, 22, 44, 0.85)',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: THEME.radius.round,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  frameTagText: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  cameraControlBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingVertical: 20,
    paddingBottom: 30,
    backgroundColor: 'rgba(7, 13, 25, 0.85)',
  },
  galleryIconBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(30, 46, 78, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  shutterButton: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 4,
    borderColor: '#2563EB',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    elevation: 8,
  },
  shutterInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#2563EB',
  },
  previewContainer: {
    padding: 20,
    alignItems: 'center',
  },
  previewImageWrapper: {
    width: '100%',
    height: 360,
    borderRadius: THEME.radius.lg,
    overflow: 'hidden',
    backgroundColor: '#050912',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  demoPlaceholder: {
    alignItems: 'center',
    padding: 20,
  },
  demoPlaceholderTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
    marginTop: 10,
  },
  demoPlaceholderSub: {
    fontSize: 12,
    color: THEME.colors.textMuted,
    marginTop: 4,
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
    width: '100%',
  },
  retakeBtn: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 14,
    borderRadius: THEME.radius.md,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  retakeBtnText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 13,
  },
  analyzeBtn: {
    flex: 1.4,
    backgroundColor: THEME.colors.accentPrimary,
    paddingVertical: 14,
    borderRadius: THEME.radius.md,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    elevation: 4,
  },
  analyzeBtnText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 13,
  },
  demoBar: {
    backgroundColor: THEME.colors.bgDark,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: THEME.colors.borderSubtle,
  },
  demoBarTitle: {
    fontSize: 9,
    fontWeight: '800',
    color: THEME.colors.textMuted,
    marginLeft: 16,
    marginBottom: 6,
    letterSpacing: 0.8,
  },
  demoScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  demoPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: THEME.radius.round,
    backgroundColor: THEME.colors.bgCard,
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  demoPillActive: {
    borderColor: THEME.colors.accentLight,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
  },
  demoPillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
    backgroundColor: THEME.colors.bgMain,
  },
  permissionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  permissionDesc: {
    fontSize: 13,
    color: THEME.colors.textSecondary,
    textAlign: 'center',
    marginVertical: 12,
    lineHeight: 18,
  },
  permissionButton: {
    backgroundColor: THEME.colors.accentPrimary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: THEME.radius.md,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  galleryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: THEME.radius.md,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
  },
  galleryButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 13,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: THEME.colors.bgMain,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  analyzingCard: {
    width: '100%',
    maxWidth: 320,
    backgroundColor: THEME.colors.bgCard,
    padding: 28,
    borderRadius: THEME.radius.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.colors.borderSubtle,
    elevation: 8,
  },
  analyzingTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  analyzingStep: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.colors.accentLight,
    marginTop: 8,
    textAlign: 'center',
  },
  analyzingSub: {
    fontSize: 11,
    color: THEME.colors.textMuted,
    marginTop: 4,
    textAlign: 'center',
  },
});

export default ScanScreen;
