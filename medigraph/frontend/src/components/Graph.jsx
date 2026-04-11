import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { getGraphData, getExploreGraph, getGraphStats } from '../services/api';
import './Graph.css';

function Graph({ selectedDisease, onNodeClick }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('explore'); // 'explore' or 'disease'

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (selectedDisease) {
      setViewMode('disease');
      loadDiseaseGraph(selectedDisease);
    } else {
      setViewMode('explore');
      loadExploreGraph();
    }
  }, [selectedDisease]);

  useEffect(() => {
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, []);

  const loadStats = async () => {
    try {
      const data = await getGraphStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadExploreGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getExploreGraph(60);
      if (data.nodes && data.nodes.length > 0) {
        initializeGraph(data);
      } else {
        // Fallback to Hypertension if explore is empty
        const data = await getGraphData('Hypertension');
        initializeGraph(data);
      }
    } catch (err) {
      setError('Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  const loadSampleGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getGraphData('Hypertension');
      initializeGraph(data);
    } catch (err) {
      setError('Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  const loadDiseaseGraph = async (disease) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getGraphData(disease);
      if (data.nodes && data.nodes.length > 0) {
        initializeGraph(data);
      } else {
        setError('No graph data available for this disease');
      }
    } catch (err) {
      setError('Failed to load disease graph');
    } finally {
      setLoading(false);
    }
  };

  const initializeGraph = (data) => {
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const elements = [
      ...data.nodes.map((node) => ({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          ...node.properties,
        },
      })),
      ...data.edges.map((edge, index) => ({
        data: {
          id: `edge-${index}`,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          ...edge.properties,
        },
      })),
    ];

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': '#3b82f6',
            color: '#1e293b',
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            width: 40,
            height: 40,
            'border-width': 2,
            'border-color': '#1d4ed8',
          },
        },
        {
          selector: 'node[type = "Disease"]',
          style: {
            'background-color': '#ef4444',
            'border-color': '#dc2626',
            width: 50,
            height: 50,
            'font-size': '14px',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node[type = "Symptom"]',
          style: {
            'background-color': '#22c55e',
            'border-color': '#16a34a',
            shape: 'ellipse',
          },
        },
        {
          selector: 'node[type = "Treatment"]',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#d97706',
            shape: 'diamond',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(type)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
          },
        },
        {
          selector: 'edge[type = "HAS_SYMPTOM"]',
          style: {
            'line-color': '#22c55e',
            'target-arrow-color': '#22c55e',
          },
        },
        {
          selector: 'edge[type = "TREATED_BY"]',
          style: {
            'line-color': '#f59e0b',
            'target-arrow-color': '#f59e0b',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#3b82f6',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        padding: 50,
      },
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      onNodeClick?.(node.data());
    });

    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        onNodeClick?.(null);
      }
    });
  };

  return (
    <div className="graph-container">
      <div className="graph-header">
        <div className="graph-title">
          <h2>Knowledge Graph</h2>
          <div className="view-badge">{viewMode === 'explore' ? 'Explore Mode' : 'Disease View'}</div>
        </div>
        <div className="header-actions">
          {selectedDisease && (
            <span className="selected-disease">{selectedDisease}</span>
          )}
          <button
            className="toggle-view-btn"
            onClick={() => {
              if (viewMode === 'explore') {
                onNodeClick?.({ type: 'explore' });
              } else {
                onNodeClick?.(null);
              }
            }}
            title={viewMode === 'explore' ? 'Switch to Disease View' : 'Switch to Explore Mode'}
          >
            {viewMode === 'explore' ? '🔍' : '🌐'}
          </button>
        </div>
      </div>

      {stats && (
        <div className="graph-stats">
          <div className="stat">
            <span className="stat-value">{stats.disease_count}</span>
            <span className="stat-label">Diseases</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.symptom_count}</span>
            <span className="stat-label">Symptoms</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.treatment_count}</span>
            <span className="stat-label">Treatments</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.relationship_count}</span>
            <span className="stat-label">Relationships</span>
          </div>
        </div>
      )}

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color disease"></span>
          <span>Disease</span>
        </div>
        <div className="legend-item">
          <span className="legend-color symptom"></span>
          <span>Symptom</span>
        </div>
        <div className="legend-item">
          <span className="legend-color treatment"></span>
          <span>Treatment</span>
        </div>
      </div>

      <div className="graph-wrapper">
        {loading && (
          <div className="graph-loading">
            <div className="spinner"></div>
            <p>Loading graph...</p>
          </div>
        )}
        {error && (
          <div className="graph-error">
            <p>{error}</p>
          </div>
        )}
        <div ref={containerRef} className="cytoscape-container" />
      </div>

      <div className="graph-controls">
        <button
          onClick={() => cyRef.current?.fit()}
          title="Fit to screen"
        >
          ⊡
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
          title="Zoom in"
        >
          +
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
          title="Zoom out"
        >
          −
        </button>
        <button
          onClick={() => cyRef.current?.stop()}
          title="Stop animation"
        >
          ⏹
        </button>
      </div>
    </div>
  );
}

export default Graph;
