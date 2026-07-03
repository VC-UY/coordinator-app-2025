import { useState } from 'react';
import { Navigate } from 'react-router';
import {
  Box,
  Button,
  Paper,
  TextField,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login({ email, password });
    } catch (err) {
      setError(err.response?.data?.detail || 'Connexion impossible.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(180deg, #001440 0%, #002060 50%, #001440 100%)',
        p: 3,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: '100%',
          maxWidth: 420,
          p: 4,
          borderRadius: 3,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.9) 0%, rgba(0, 20, 64, 0.9) 100%)',
          border: '2px solid rgba(0, 180, 240, 0.35)',
        }}
      >
        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 800, mb: 1 }}>
          VolunSys Coordinateur
        </Typography>
        <Typography sx={{ color: '#00B0F0', mb: 3, fontSize: 14 }}>
          Connexion securisee a l interface d orchestration
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            fullWidth
            InputLabelProps={{ style: { color: '#94a3b8' } }}
            sx={{ input: { color: '#fff' } }}
          />
          <TextField
            label="Mot de passe"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            fullWidth
            InputLabelProps={{ style: { color: '#94a3b8' } }}
            sx={{ input: { color: '#fff' } }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            sx={{
              mt: 1,
              py: 1.4,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #00B0F0 0%, #00D4FF 100%)',
            }}
          >
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Se connecter'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
