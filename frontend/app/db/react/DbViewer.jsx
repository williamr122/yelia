'use client';

import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../../_shared/react/api.js';
import { notify } from '../../chat/react/core/notify.js';

function tableName(item) {
  return typeof item === 'string' ? item : item?.name;
}

function cellPreview(value) {
  if (value === null || value === undefined || value === '') return '-';
  const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

function fullValue(value) {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

export default function DbViewer() {
  const [tables, setTables] = useState([]);
  const [table, setTable] = useState('');
  const [schema, setSchema] = useState([]);
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState('');
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [selectedRow, setSelectedRow] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tableFilter, setTableFilter] = useState('');
  const [tablesCollapsed, setTablesCollapsed] = useState(false);
  const [dbEngine, setDbEngine] = useState('');

  const cols = useMemo(
    () => schema.map((c) => (typeof c === 'string' ? c : (c.name || c.column || c))).filter(Boolean),
    [schema],
  );

  const filteredTables = useMemo(() => {
    const needle = tableFilter.trim().toLowerCase();
    return tables.filter((item) => !needle || String(tableName(item) || '').toLowerCase().includes(needle));
  }, [tables, tableFilter]);

  const detailEntries = useMemo(() => {
    if (!selectedRow) return [];
    const rowKeys = Object.keys(selectedRow);
    const orderedKeys = [...cols, ...rowKeys.filter((key) => !cols.includes(key))];
    return orderedKeys.map((key) => [key, selectedRow[key]]);
  }, [selectedRow, cols]);

  async function loadTables() {
    try {
      api.get('/api/db/health').then((health) => setDbEngine(health.db_engine || health.engine || '')).catch(() => setDbEngine(''));
      const data = await api.get('/api/db/tables');
      const arr = data.tables || data.items || [];
      setTables(arr);
      const first = tableName(arr[0]);
      if (!table && first) setTable(first);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  const engineTitle = dbEngine === 'postgresql' ? 'PostgreSQL' : dbEngine === 'sqlite' ? 'SQLite local' : 'base de datos';

  async function loadRows(nextTable = table, nextOffset = offset) {
    if (!nextTable) return;
    setLoading(true);
    setSelectedRow(null);
    setSelectedIndex(null);
    try {
      const schemaData = await api.get(`/api/db/schema/${encodeURIComponent(nextTable)}`);
      setSchema(schemaData.columns || schemaData.schema || []);
      const query = new URLSearchParams({
        limit: String(limit),
        offset: String(nextOffset),
        q,
      });
      const data = await api.get(`/api/db/table/${encodeURIComponent(nextTable)}?${query.toString()}`);
      setRows(data.rows || data.items || []);
      setOffset(nextOffset);
    } catch (error) {
      notify(error.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  function chooseTable(nextTable) {
    if (!nextTable) return;
    setTable(nextTable);
    setOffset(0);
    setSelectedRow(null);
    setSelectedIndex(null);
  }

  function chooseRow(row, index) {
    setSelectedRow(row);
    setSelectedIndex(index);
  }

  useLayoutEffect(() => {
    document.body.className = 'p-3 p-md-4 desktop-pro db-viewer-page';
    loadTables();
  }, []);

  useEffect(() => {
    if (table) loadRows(table, 0);
  }, [table, limit]);

  return (
    <div className="db-viewer-shell">
      <div className={`db-viewer-layout ${tablesCollapsed ? 'is-table-collapsed' : ''}`}>
        <aside className="glass rounded-4 p-3 db-table-panel">
          <button
            className="db-table-collapse"
            onClick={() => setTablesCollapsed((value) => !value)}
            type="button"
            title={tablesCollapsed ? 'Mostrar tablas' : 'Ocultar tablas'}
            aria-label={tablesCollapsed ? 'Mostrar tablas' : 'Ocultar tablas'}
          >
            <i className={`bi ${tablesCollapsed ? 'bi-chevron-right' : 'bi-chevron-left'}`}></i>
          </button>
          <div className="db-panel-title">
            <b>Tablas</b>
            <button className="btn btn-sm btn-outline-light" onClick={loadTables} type="button" title="Recargar tablas">
              <i className="bi bi-arrow-clockwise"></i>
            </button>
          </div>
          <div className="db-table-filter">
            <i className="bi bi-search"></i>
            <input value={tableFilter} onChange={(e) => setTableFilter(e.target.value)} placeholder="filtrar tablas..." />
          </div>
          <div className="db-table-list">
            {filteredTables.map((item, index) => {
              const name = tableName(item);
              const active = table === name;
              return (
                <button
                  key={name || index}
                  className={`db-table-button ${active ? 'active' : ''}`}
                  onClick={() => chooseTable(name)}
                  type="button"
                >
                  <span><i className="bi bi-table"></i>{name}</span>
                  <em>table</em>
                </button>
              );
            })}
          </div>
          <small className="muted d-block mt-2">Tabla actual: <b>{table || 'ninguna'}</b></small>
        </aside>

        <section className="db-main-panel">
          <div className="topbar glass rounded-4 p-3 mb-3 db-viewer-topbar">
            <div>
              <div className="fs-4 fw-bold">Visor de Base de Datos ({engineTitle})</div>
              <div className="muted">Solo lectura. Selecciona una tabla y haz click en una fila para ver el registro completo.</div>
            </div>
            <div className="d-flex gap-2">
              <button className="btn btn-outline-light" onClick={() => loadRows(table, offset)} type="button">
                <i className="bi bi-arrow-clockwise"></i> Actualizar
              </button>
              <a className="btn btn-outline-light" href="/admin">
                <i className="bi bi-speedometer2"></i> Volver a Admin
              </a>
            </div>
          </div>

            <div className="glass rounded-4 p-3 mb-3 db-query-panel">
              <span className="db-chip">Busqueda de registros</span>
              <div className="db-query-grid">
                <label>
                  <b>Buscar</b>
                  <div className="db-search-input">
                    <i className="bi bi-search"></i>
                    <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="texto a buscar..." />
                    {q && <button onClick={() => setQ('')} type="button" aria-label="Limpiar busqueda"><i className="bi bi-x-lg"></i></button>}
                  </div>
                </label>
                <label>
                  <b>Filas por pagina</b>
                  <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                    <option value="200">200</option>
                  </select>
                </label>
                <button className="btn btn-primary" onClick={() => loadRows(table, 0)} type="button">
                  <i className="bi bi-arrow-repeat"></i> Cargar
                </button>
              </div>
              <small className="muted">Busca en todas las columnas disponibles de la tabla seleccionada.</small>
            </div>

          {selectedRow ? (
            <div className="glass rounded-4 p-3 db-detail-view">
              <div className="db-detail-head">
                <div>
                  <span className="db-chip">Detalle completo</span>
                  <h2>{table}</h2>
                  <p className="muted">Registro #{offset + selectedIndex + 1}. Todos los campos se muestran completos.</p>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-outline-light" onClick={() => setSelectedRow(null)} type="button">
                    <i className="bi bi-arrow-left"></i> Volver a registros
                  </button>
                </div>
              </div>
              <div className="db-detail-grid">
                {detailEntries.map(([col, value]) => (
                  <article className="db-detail-field" key={col}>
                    <strong>{col}</strong>
                    <pre>{fullValue(value)}</pre>
                  </article>
                ))}
              </div>
            </div>
          ) : (
            <div className="glass rounded-4 p-3 db-records-panel">
              <div className="db-records-head">
                <div>
                  <b>Registros</b>
                  <p className="muted small mb-0">{table ? `Tabla: ${table}` : 'Selecciona una tabla para comenzar.'}</p>
                </div>
                <div className="db-pager">
                  <button className="btn btn-sm btn-outline-light" disabled={offset <= 0 || loading} onClick={() => loadRows(table, Math.max(0, offset - Number(limit)))} type="button">
                    <i className="bi bi-chevron-left"></i>
                  </button>
                  <button className="btn btn-sm btn-outline-light" disabled={loading || rows.length < Number(limit)} onClick={() => loadRows(table, offset + Number(limit))} type="button">
                    <i className="bi bi-chevron-right"></i>
                  </button>
                  <span className="muted small">Mostrando {rows.length ? offset + 1 : 0}-{offset + rows.length}</span>
                </div>
              </div>

              <div className="table-wrap db-table-wrap">
                <div className="table-responsive">
                  <table className="table table-sm table-pro db-data-table">
                    <thead>
                      <tr>{cols.map((col) => <th key={col}>{col}</th>)}</tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr><td colSpan={cols.length || 1} className="text-center muted">Cargando registros...</td></tr>
                      ) : rows.length ? (
                        rows.map((row, index) => (
                          <tr key={`${table}-${offset}-${index}`} onClick={() => chooseRow(row, index)} tabIndex={0} role="button">
                            {cols.map((col) => <td key={col}>{cellPreview(row[col])}</td>)}
                          </tr>
                        ))
                      ) : (
                        <tr><td colSpan={cols.length || 1} className="text-center muted">Sin datos</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
              <p className="db-table-hint">Tip: haz click en cualquier fila para abrir el detalle completo del registro.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
