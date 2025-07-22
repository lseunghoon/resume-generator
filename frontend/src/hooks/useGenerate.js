import { useState } from 'react';
import { upload, generate, revise } from '../services/api';

export default function useGenerate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const uploadData = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await upload(formData);
      return res.data;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const generateData = async (session_id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await generate(session_id);
      return res.data;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const reviseData = async (session_id, q_idx, prompt) => {
    setLoading(true);
    setError(null);
    try {
      const res = await revise(session_id, q_idx, prompt);
      return res.data;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { uploadData, generateData, reviseData, loading, error };
} 