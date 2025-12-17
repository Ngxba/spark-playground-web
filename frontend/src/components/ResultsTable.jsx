import { useState, useMemo } from 'react';
import './ResultsTable.css';

function ResultsTable({ output, expectedOutput, correct }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [searchTerm, setSearchTerm] = useState('');

  const parseOutput = (data) => {
    if (!data) return [];

    if (Array.isArray(data)) {
      return data;
    }

    if (typeof data === 'string') {
      try {
        return JSON.parse(data);
      } catch {
        return [];
      }
    }

    return [];
  };

  const rows = parseOutput(output);
  const expectedRows = parseOutput(expectedOutput);

  const columns = useMemo(() => {
    if (rows.length === 0) return [];
    return Object.keys(rows[0]);
  }, [rows]);

  const filteredRows = useMemo(() => {
    if (!searchTerm) return rows;

    return rows.filter((row) => {
      return Object.values(row).some((value) =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [rows, searchTerm]);

  const sortedRows = useMemo(() => {
    if (!sortConfig.key) return filteredRows;

    const sorted = [...filteredRows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === bVal) return 0;

      const comparison = aVal > bVal ? 1 : -1;
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [filteredRows, sortConfig]);

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return '⇅';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  const isRowDifferent = (index) => {
    if (correct || !expectedRows || expectedRows.length === 0) return false;
    if (index >= expectedRows.length) return true;

    const actualRow = rows[index];
    const expectedRow = expectedRows[index];

    return JSON.stringify(actualRow) !== JSON.stringify(expectedRow);
  };

  if (rows.length === 0) {
    return (
      <div className="results-table-container">
        <p className="no-data">No output data available</p>
      </div>
    );
  }

  return (
    <div className="results-table-container">
      <div className="table-controls">
        <div className="table-info">
          <span className="row-count">
            {sortedRows.length} {sortedRows.length === 1 ? 'row' : 'rows'}
          </span>
          {sortedRows.length !== rows.length && (
            <span className="filtered-info">
              (filtered from {rows.length})
            </span>
          )}
        </div>
        <input
          type="text"
          className="table-search"
          placeholder="Search in results..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} onClick={() => handleSort(col)}>
                  <div className="th-content">
                    <span>{col}</span>
                    <span className="sort-icon">{getSortIcon(col)}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, i) => (
              <tr
                key={i}
                className={isRowDifferent(i) ? 'row-different' : ''}
              >
                {columns.map((col) => (
                  <td key={col}>{String(row[col] ?? '')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!correct && expectedRows.length > 0 && (
        <div className="diff-view">
          <h4>Expected Output</h4>
          <div className="table-wrapper">
            <table className="results-table expected-table">
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {expectedRows.map((row, i) => (
                  <tr key={i}>
                    {columns.map((col) => (
                      <td key={col}>{String(row[col] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultsTable;
