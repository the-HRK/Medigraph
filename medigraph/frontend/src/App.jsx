import { useState } from 'react';
import Chat from './components/Chat';
import Graph from './components/Graph';
import './App.css';

function App() {
  const [selectedDisease, setSelectedDisease] = useState(null);

  const handleDiseaseSelect = (diseaseName) => {
    if (diseaseName) {
      setSelectedDisease(diseaseName);
    }
  };

  const handleNodeClick = (nodeData) => {
    if (nodeData && nodeData.type === 'Disease') {
      setSelectedDisease(nodeData.label);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🩺</span>
          <h1>Medigraph</h1>
        </div>
        <p className="tagline">Healthcare Knowledge Graph</p>
      </header>

      <main className="app-main">
        <div className="split-view">
          <div className="chat-panel">
            <Chat onDiseaseSelect={handleDiseaseSelect} />
          </div>
          <div className="graph-panel">
            <Graph
              selectedDisease={selectedDisease}
              onNodeClick={handleNodeClick}
            />
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Powered by Neo4j Graph Database |{' '}
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            API Documentation
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
