import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Grid, CircularProgress, List, ListItem, ListItemText, Divider } from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import api from '../services/api';

export default function NoteAssistant() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/notes/upload-audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Note Assistant</Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Upload Classroom Audio</Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Button
            component="label"
            variant="outlined"
            startIcon={<CloudUploadIcon />}
          >
            Select Audio File
            <input type="file" hidden onChange={handleFileChange} accept="audio/*" />
          </Button>
          <Typography>{file ? file.name : 'No file selected'}</Typography>
          <Button 
            variant="contained" 
            onClick={handleUpload} 
            disabled={!file || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Process'}
          </Button>
        </Box>
      </Paper>

      {result && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Transcript</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.transcript}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Structured Notes</Typography>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                {result.structured_notes.title}
              </Typography>
              
              <Typography variant="subtitle2" sx={{ mt: 2 }}>Key Points:</Typography>
              <List dense>
                {result.structured_notes.key_points?.map((point, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${point}`} />
                  </ListItem>
                ))}
              </List>

              <Typography variant="subtitle2" sx={{ mt: 2 }}>Examples:</Typography>
              <List dense>
                {result.structured_notes.examples?.map((ex, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${ex}`} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
