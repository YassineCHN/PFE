import React from 'react';
import OccupancyDashboard from './components/OccupancyDashboard';

function App() {
  return (
    <div className="container mt-4">
      <h1 className="mb-4">Tableau de Bord d'Occupation des Trains SNCF</h1>
      <OccupancyDashboard />
    </div>
  );
}

export default App;