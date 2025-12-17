import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { analyzeAndExecute } from '../lib/api';

export default function ScanScreen() {
  const [image, setImage] = useState<string | null>(null);
  const [intent, setIntent] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const requestCameraPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Camera permission is required to scan');
      return false;
    }
    return true;
  };

  const takePhoto = async () => {
    const hasPermission = await requestCameraPermission();
    if (!hasPermission) return;

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImage(result.assets[0].uri);
      setError(null);
      setResult(null);
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImage(result.assets[0].uri);
      setError(null);
      setResult(null);
    }
  };

  const handleSubmit = async () => {
    if (!image || !intent.trim()) {
      Alert.alert('Error', 'Please select an image and enter your intent');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeAndExecute(image, intent);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      Alert.alert('Error', err.message || 'Failed to process request');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setIntent('');
    setResult(null);
    setError(null);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>HealthScan</Text>
        <Text style={styles.subtitle}>Your AI healthcare assistant</Text>
      </View>

      {/* Image Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>1. Capture or Upload Image</Text>
        {image ? (
          <View style={styles.imageContainer}>
            <Image source={{ uri: image }} style={styles.image} />
            <TouchableOpacity onPress={handleReset} style={styles.changeButton}>
              <Text style={styles.changeButtonText}>Change image</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.buttonRow}>
            <TouchableOpacity onPress={takePhoto} style={styles.captureButton}>
              <Text style={styles.buttonText}>📷 Take Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={pickImage} style={styles.uploadButton}>
              <Text style={styles.buttonText}>📁 Choose from Library</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Intent Input */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>2. What do you need help with?</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Fill out this patient form, Book an appointment, Read this prescription"
          placeholderTextColor="#999"
          value={intent}
          onChangeText={setIntent}
          multiline
          numberOfLines={3}
        />
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        onPress={handleSubmit}
        disabled={loading || !image || !intent.trim()}
        style={[styles.submitButton, (!image || !intent.trim()) && styles.submitButtonDisabled]}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>Scan & Help</Text>
        )}
      </TouchableOpacity>

      {/* Error */}
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Results */}
      {result && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Results</Text>
          <View style={styles.resultContainer}>
            <Text style={styles.resultStatus}>Status: {result.status}</Text>
            {result.plan && (
              <View style={styles.resultSection}>
                <Text style={styles.resultLabel}>Plan:</Text>
                <Text style={styles.resultText}>{JSON.stringify(result.plan, null, 2)}</Text>
              </View>
            )}
            {result.execution && (
              <View style={styles.resultSection}>
                <Text style={styles.resultLabel}>Execution:</Text>
                <Text style={styles.resultText}>{JSON.stringify(result.execution, null, 2)}</Text>
              </View>
            )}
            <TouchableOpacity onPress={handleReset} style={styles.resetButton}>
              <Text style={styles.resetButtonText}>Start over</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    padding: 20,
    alignItems: 'center',
    paddingTop: 60,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#999',
  },
  section: {
    backgroundColor: '#1a1a1a',
    margin: 16,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  captureButton: {
    flex: 1,
    backgroundColor: '#0066CC',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  uploadButton: {
    flex: 1,
    backgroundColor: '#333',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  imageContainer: {
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: 300,
    borderRadius: 8,
    marginBottom: 12,
  },
  changeButton: {
    padding: 8,
  },
  changeButtonText: {
    color: '#00ff88',
    fontSize: 14,
  },
  input: {
    backgroundColor: '#0a0a0a',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 16,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#0066CC',
    margin: 16,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#333',
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  errorContainer: {
    backgroundColor: '#4a0000',
    borderWidth: 1,
    borderColor: '#ff0000',
    margin: 16,
    padding: 16,
    borderRadius: 8,
  },
  errorText: {
    color: '#ff6666',
  },
  resultContainer: {
    marginTop: 12,
  },
  resultStatus: {
    color: '#0066CC',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  resultSection: {
    marginBottom: 16,
  },
  resultLabel: {
    color: '#999',
    fontSize: 14,
    marginBottom: 4,
  },
  resultText: {
    color: '#fff',
    fontSize: 12,
    fontFamily: 'monospace',
    backgroundColor: '#0a0a0a',
    padding: 12,
    borderRadius: 4,
  },
  resetButton: {
    marginTop: 12,
    padding: 8,
  },
  resetButtonText: {
    color: '#999',
    fontSize: 14,
  },
});

