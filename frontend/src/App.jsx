import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NoteAssistant from './pages/NoteAssistant';
import MapGeneration from './pages/MapGeneration';
import ErrorBook from './pages/ErrorBook';
import ParentView from './pages/ParentView';
import Login from './pages/Login';
import Register from './pages/Register';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="notes" element={<NoteAssistant />} />
        <Route path="maps" element={<MapGeneration />} />
        <Route path="errors" element={<ErrorBook />} />
        <Route path="parents" element={<ParentView />} />
      </Route>
    </Routes>
  );
}

export default App;
