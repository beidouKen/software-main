import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Paper, Grid, CircularProgress, Card, CardContent, Chip, Divider, TextField, ButtonGroup, IconButton, Tooltip, Dialog, DialogContent } from '@mui/material';
import { CloudUpload as CloudUploadIcon, FormatBold, FormatItalic, FormatSize, Code, Close as CloseIcon } from '@mui/icons-material';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export default function ErrorBook() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  
  // Student solution state
  const [studentFile, setStudentFile] = useState(null);
  const [studentPreviewUrl, setStudentPreviewUrl] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  // Editable analysis state
  const [editableAnalysis, setEditableAnalysis] = useState('');

  // Image Zoom State
  const [zoomImage, setZoomImage] = useState(null);

  // OCR State
  const [ocrText, setOcrText] = useState('');
  const [ocrLoading, setOcrLoading] = useState(false);

  const performOCR = async (selectedFile) => {
    setOcrLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await api.post('/errors/ocr', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setOcrText(response.data.text);
    } catch (error) {
      console.error('Error performing OCR:', error);
      alert('OCR failed. Please try again.');
    } finally {
      setOcrLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      performOCR(selectedFile);
    }
  };

  const handleStudentFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setStudentFile(selectedFile);
      setStudentPreviewUrl(URL.createObjectURL(selectedFile));
    }
  };

  const handleAnalyze = async () => {
    if (!ocrText) return;

    setLoading(true);
    
    try {
      const response = await api.post('/errors/analyze', { text: ocrText });
      setResult(response.data);
      // Initialize editable analysis with the result
      setEditableAnalysis(response.data.analysis.explanation);
    } catch (error) {
      console.error('Error analyzing problem:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Analysis failed';
      alert(`Analysis failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const insertText = (before, after = '') => {
    const textarea = document.getElementById('analysis-editor');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = editableAnalysis;
    const newText = text.substring(0, start) + before + text.substring(start, end) + after + text.substring(end);
    
    setEditableAnalysis(newText);
    
    // Restore focus and selection (approximate)
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + before.length, end + before.length);
    }, 0);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Error Book Manager</Typography>
      
      <Grid container spacing={3}>
        {/* Problem Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>1. Upload Problem Image</Typography>
            <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
              <Button
                component="label"
                variant="outlined"
                startIcon={<CloudUploadIcon />}
              >
                Select Problem
                <input type="file" hidden onChange={handleFileChange} accept="image/*" />
              </Button>
              <Typography noWrap sx={{ maxWidth: 200 }}>{file ? file.name : 'No file selected'}</Typography>
            </Box>
            
            {previewUrl && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', bgcolor: '#f0f0f0', p: 1, borderRadius: 1, cursor: 'pointer' }} onClick={() => setZoomImage(previewUrl)}>
                <img 
                  src={previewUrl} 
                  alt="Problem Preview" 
                  style={{ maxWidth: '100%', maxHeight: '200px', objectFit: 'contain' }} 
                />
                <Typography variant="caption" sx={{ position: 'absolute', mt: 24, color: 'text.secondary' }}>Click to enlarge</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Student Solution Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>2. Upload Your Solution (Optional)</Typography>
            <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
              <Button
                component="label"
                variant="outlined"
                color="secondary"
                startIcon={<CloudUploadIcon />}
              >
                Select Solution
                <input type="file" hidden onChange={handleStudentFileChange} accept="image/*" />
              </Button>
              <Typography noWrap sx={{ maxWidth: 200 }}>{studentFile ? studentFile.name : 'No file selected'}</Typography>
            </Box>
            
            {studentPreviewUrl && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', bgcolor: '#f0f0f0', p: 1, borderRadius: 1, cursor: 'pointer' }} onClick={() => setZoomImage(studentPreviewUrl)}>
                <img 
                  src={studentPreviewUrl} 
                  alt="Solution Preview" 
                  style={{ maxWidth: '100%', maxHeight: '200px', objectFit: 'contain' }} 
                />
                <Typography variant="caption" sx={{ position: 'absolute', mt: 24, color: 'text.secondary' }}>Click to enlarge</Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* OCR Result Section */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              3. Verify & Edit OCR Text
              {ocrLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
            </Typography>
            <TextField
              multiline
              fullWidth
              minRows={4}
              maxRows={15}
              value={ocrText}
              onChange={(e) => setOcrText(e.target.value)}
              placeholder={ocrLoading ? "Extracting text..." : "OCR text will appear here. You can edit it before analysis."}
              disabled={ocrLoading}
              variant="outlined"
            />
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
        <Button 
          variant="contained" 
          size="large"
          onClick={handleAnalyze} 
          disabled={!ocrText || loading || ocrLoading}
          sx={{ minWidth: 200 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Analyze Problem'}
        </Button>
      </Box>

      {result && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h5">AI Analysis & Correction</Typography>
                  <Box>
                    <Chip label={result.analysis.topic} color="primary" sx={{ mr: 1 }} />
                    <Chip label={result.analysis.difficulty} color="secondary" />
                  </Box>
                </Box>

                <Grid container spacing={2}>
                  {/* Editor Side */}
                  <Grid item xs={12} md={6}>
                    <Paper variant="outlined" sx={{ p: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, mb: 1 }}>
                        <ButtonGroup size="small" variant="text">
                          <Tooltip title="Bold"><IconButton onClick={() => insertText('**', '**')}><FormatBold /></IconButton></Tooltip>
                          <Tooltip title="Italic"><IconButton onClick={() => insertText('*', '*')}><FormatItalic /></IconButton></Tooltip>
                          <Tooltip title="Large Text"><IconButton onClick={() => insertText('# ')}><FormatSize /></IconButton></Tooltip>
                          <Tooltip title="Inline Math"><IconButton onClick={() => insertText('$', '$')}><Code /></IconButton></Tooltip>
                          <Tooltip title="Block Math"><IconButton onClick={() => insertText('$$', '$$')}><Code /></IconButton></Tooltip>
                        </ButtonGroup>
                      </Box>
                      <TextField
                        id="analysis-editor"
                        multiline
                        fullWidth
                        minRows={15}
                        value={editableAnalysis}
                        onChange={(e) => setEditableAnalysis(e.target.value)}
                        variant="standard"
                        InputProps={{ disableUnderline: true }}
                        sx={{ flexGrow: 1, fontFamily: 'monospace' }}
                        placeholder="Analysis content..."
                      />
                    </Paper>
                  </Grid>

                  {/* Preview Side */}
                  <Grid item xs={12} md={6}>
                    <Paper variant="outlined" sx={{ p: 2, height: '100%', minHeight: '400px', bgcolor: '#fafafa', overflow: 'auto' }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Preview</Typography>
                      <Box className="markdown-preview">
                        <ReactMarkdown 
                          remarkPlugins={[remarkMath]} 
                          rehypePlugins={[rehypeKatex]}
                        >
                          {editableAnalysis}
                        </ReactMarkdown>
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />
                
                <Typography variant="h6" gutterBottom>Similar Question:</Typography>
                <Paper sx={{ p: 2, bgcolor: '#f8f9fa' }}>
                  <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                    {result.analysis.similar_question}
                  </ReactMarkdown>
                </Paper>

              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Image Zoom Dialog */}
      <Dialog 
        open={!!zoomImage} 
        onClose={() => setZoomImage(null)}
        maxWidth="lg"
        fullWidth
      >
        <Box sx={{ position: 'relative', p: 1, bgcolor: 'black', display: 'flex', justifyContent: 'center' }}>
          <IconButton 
            onClick={() => setZoomImage(null)}
            sx={{ position: 'absolute', right: 8, top: 8, color: 'white', bgcolor: 'rgba(0,0,0,0.5)' }}
          >
            <CloseIcon />
          </IconButton>
          <img 
            src={zoomImage} 
            alt="Full size" 
            style={{ maxWidth: '100%', maxHeight: '90vh', objectFit: 'contain' }} 
          />
        </Box>
      </Dialog>
    </Box>
  );
}
