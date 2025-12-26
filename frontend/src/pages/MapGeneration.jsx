import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, TextField, Button, Paper } from '@mui/material';
import mermaid from 'mermaid';
import api from '../services/api';

mermaid.initialize({ startOnLoad: true });

export default function MapGeneration() {
  const [content, setContent] = useState('');
  const [mermaidCode, setMermaidCode] = useState('');
  const [loading, setLoading] = useState(false);
  const mermaidRef = useRef(null);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await api.post('/maps/generate', { content });
      setMermaidCode(response.data.mermaid_source);
    } catch (error) {
      console.error('Error generating map:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mermaidCode && mermaidRef.current) {
      mermaidRef.current.innerHTML = mermaidCode;
      mermaidRef.current.removeAttribute('data-processed');
      mermaid.run({
        nodes: [mermaidRef.current]
      });
    }
  }, [mermaidCode]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Mind Map Generator</Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <TextField
          label="Paste your notes here"
          multiline
          rows={4}
          fullWidth
          value={content}
          onChange={(e) => setContent(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Button variant="contained" onClick={handleGenerate} disabled={loading || !content}>
          {loading ? 'Generating...' : 'Generate Map'}
        </Button>
      </Paper>

      {mermaidCode && (
        <Paper sx={{ p: 3, overflowX: 'auto' }}>
          <Typography variant="h6" gutterBottom>Visualized Map</Typography>
          <div className="mermaid" ref={mermaidRef}>
            {mermaidCode}
          </div>
        </Paper>
      )}
    </Box>
  );
}
