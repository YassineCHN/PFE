// Extraction des composants de Recharts
const {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
    Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
  } = Recharts;
  
  // Composant principal du tableau de bord
  function OccupancyDashboard() {
    const [trainNumber, setTrainNumber] = React.useState('9577');
    const [journeyDate, setJourneyDate] = React.useState('2024-12-11');
    const [globalData, setGlobalData] = React.useState(null);
    const [desserteData, setDesserteData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
  
    React.useEffect(() => {
      // Charger les données initiales
      loadData();
    }, []);
  
    const loadData = async () => {
      setLoading(true);
      setError(null);
  
      try {
        // Charger les données globales
        const globalResponse = await axios.get(`/API/tauxOccupation/${trainNumber}&${journeyDate}`);
        setGlobalData(globalResponse.data);
  
        // Charger les données par desserte
        const desserteResponse = await axios.get(`/API/tauxOccupationDesserte/${trainNumber}&${journeyDate}`);
        setDesserteData(desserteResponse.data);
  
        setLoading(false);
      } catch (err) {
        setError(`Erreur lors du chargement des données: ${err.message}`);
        setLoading(false);
      }
    };
  
    const handleSubmit = (e) => {
      e.preventDefault();
      loadData();
    };
  
    // Couleurs pour les graphiques
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
  
    // Formatage des données pour les graphiques d'occupation par station
    const getStationOccupancyData = () => {
      if (!desserteData || !desserteData.desserte_occupation) return [];
  
      return desserteData.desserte_occupation.map(station => ({
        name: station.station_name,
        occupationRate: station.occupation_rate,
        totalSeats: station.total_seats,
        occupiedSeats: station.occupied_seats
      }));
    };
  
    // Formatage des données pour les graphiques d'occupation par voiture
    const getCoachOccupancyData = () => {
      if (!desserteData || !desserteData.desserte_occupation) return [];
  
      // Calculer la moyenne d'occupation par voiture sur tout le trajet
      const coachData = {};
      
      desserteData.desserte_occupation.forEach(station => {
        station.coach_occupation.forEach(coach => {
          if (!coachData[coach.coach_number]) {
            coachData[coach.coach_number] = {
              totalOccupancy: 0,
              count: 0
            };
          }
          coachData[coach.coach_number].totalOccupancy += coach.occupation_rate;
          coachData[coach.coach_number].count += 1;
        });
      });
      
      return Object.entries(coachData).map(([coach, data]) => ({
        name: `Voiture ${coach}`,
        value: data.totalOccupancy / data.count
      }));
    };
  
    // Rendu conditionnel en fonction de l'état du chargement
    if (loading) {
      return (
        <div className="d-flex justify-content-center my-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Chargement...</span>
          </div>
        </div>
      );
    }
  
    if (error) {
      return (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      );
    }
  
    return (
      <div>
        {/* Formulaire de sélection */}
        <div className="card mb-4">
          <div className="card-body">
            <h5 className="card-title">Sélectionner un train</h5>
            <form onSubmit={handleSubmit} className="row g-3">
              <div className="col-md-5">
                <label htmlFor="trainNumber" className="form-label">Numéro de train</label>
                <input
                  type="text"
                  className="form-control"
                  id="trainNumber"
                  value={trainNumber}
                  onChange={(e) => setTrainNumber(e.target.value)}
                  required
                />
              </div>
              <div className="col-md-5">
                <label htmlFor="journeyDate" className="form-label">Date (YYYY-MM-DD)</label>
                <input
                  type="text"
                  className="form-control"
                  id="journeyDate"
                  value={journeyDate}
                  onChange={(e) => setJourneyDate(e.target.value)}
                  required
                />
              </div>
              <div className="col-md-2 d-flex align-items-end">
                <button type="submit" className="btn btn-primary w-100">Rechercher</button>
              </div>
            </form>
          </div>
        </div>
  
        {globalData && (
          <>
            {/* Cartes KPI */}
            <div className="row mb-4">
              <div className="col-md-4">
                <div className="card text-center h-100">
                  <div className="card-body">
                    <h5 className="card-title">Taux d'occupation global</h5>
                    <p className="display-3 text-primary mb-0">{globalData.occupation_rate}%</p>
                    <p className="text-muted">{globalData.occupied_seats} / {globalData.total_seats} sièges</p>
                  </div>
                </div>
              </div>
              <div className="col-md-4">
                <div className="card text-center h-100">
                  <div className="card-body">
                    <h5 className="card-title">Train</h5>
                    <p className="display-3 text-info mb-0">{globalData.train_number}</p>
                    <p className="text-muted">Date: {globalData.journey_date}</p>
                  </div>
                </div>
              </div>
              <div className="col-md-4">
                <div className="card text-center h-100">
                  <div className="card-body">
                    <h5 className="card-title">Actions</h5>
                    <a href={`/API/exportCSV/${trainNumber}&${journeyDate}`} className="btn btn-success mb-2 w-100">
                      Exporter CSV
                    </a>
                    <a href="/gestionnaire/" className="btn btn-outline-secondary w-100">
                      Vue détaillée
                    </a>
                  </div>
                </div>
              </div>
            </div>
  
            {/* Graphiques */}
            <div className="row mb-4">
              {/* Graphique d'occupation par station */}
              <div className="col-md-8">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title">Taux d'occupation par station</h5>
                    <div style={{ height: '400px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={getStationOccupancyData()}
                          margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="name" 
                            angle={-45} 
                            textAnchor="end" 
                            height={90} 
                            interval={0}
                          />
                          <YAxis 
                            label={{ value: 'Taux d\'occupation (%)', angle: -90, position: 'insideLeft' }}
                          />
                          <Tooltip 
                            formatter={(value, name) => [`${value.toFixed(2)}%`, 'Taux d\'occupation']}
                            labelFormatter={(label) => `Station: ${label}`}
                          />
                          <Legend />
                          <Bar 
                            dataKey="occupationRate" 
                            fill="#0088FE" 
                            name="Taux d'occupation"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
  
              {/* Graphique d'occupation par voiture */}
              <div className="col-md-4">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title">Occupation moyenne par voiture</h5>
                    <div style={{ height: '400px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={getCoachOccupancyData()}
                            cx="50%"
                            cy="50%"
                            labelLine={true}
                            label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {getCoachOccupancyData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  
            {/* Evolution du taux d'occupation sur le trajet */}
            <div className="card mb-4">
              <div className="card-body">
                <h5 className="card-title">Évolution du taux d'occupation</h5>
                <div style={{ height: '300px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={getStationOccupancyData()}
                      margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis 
                        domain={[0, 100]} 
                        label={{ value: 'Taux d\'occupation (%)', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip 
                        formatter={(value, name) => [`${value.toFixed(2)}%`, 'Taux d\'occupation']}
                        labelFormatter={(label) => `Station: ${label}`}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="occupationRate" 
                        stroke="#FF8042" 
                        activeDot={{ r: 8 }} 
                        strokeWidth={2}
                        name="Taux d'occupation"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
  
            {/* Tableau des données détaillées */}
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Données détaillées par station</h5>
                <div className="table-responsive">
                  <table className="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>Station</th>
                        <th>Places occupées</th>
                        <th>Places totales</th>
                        <th>Taux d'occupation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {desserteData && desserteData.desserte_occupation.map((station, index) => (
                        <tr key={index}>
                          <td>{station.station_name}</td>
                          <td>{station.occupied_seats}</td>
                          <td>{station.total_seats}</td>
                          <td>{station.occupation_rate.toFixed(2)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }
  
  // Rendez le composant principal dans l'élément root
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(React.createElement(OccupancyDashboard));