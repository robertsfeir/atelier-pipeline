/**
 * Mock pg.Pool for brain module unit tests.
 * Records queries and returns configurable results.
 */

/**
 * Creates a mock pg.Pool that tracks queries and returns pre-configured results.
 *
 * Usage:
 *   const pool = createMockPool();
 *   pool.setQueryResult('SELECT 1', { rows: [{ one: 1 }], rowCount: 1 });
 *   const result = await pool.query('SELECT 1');
 *   assert.deepStrictEqual(result.rows, [{ one: 1 }]);
 *   assert.strictEqual(pool.queries.length, 1);
 */
function createMockPool() {
  const queries = [];
  const queryResults = new Map();
  let defaultResult = { rows: [], rowCount: 0 };

  function setQueryResult(sqlPattern, result) {
    queryResults.set(sqlPattern, result);
  }

  function setDefaultResult(result) {
    defaultResult = result;
  }

  function findResult(sql) {
    for (const [pattern, result] of queryResults.entries()) {
      if (typeof pattern === 'string' && sql.includes(pattern)) {
        return typeof result === 'function' ? result(sql) : result;
      }
      if (pattern instanceof RegExp && pattern.test(sql)) {
        return typeof result === 'function' ? result(sql) : result;
      }
    }
    return defaultResult;
  }

  async function query(sql, params) {
    queries.push({ sql, params });
    const result = findResult(sql);
    if (result instanceof Error) throw result;
    return result;
  }

  function createMockClient() {
    const clientQueries = [];

    async function clientQuery(sql, params) {
      clientQueries.push({ sql, params });
      queries.push({ sql, params });
      const result = findResult(sql);
      if (result instanceof Error) throw result;
      return result;
    }

    return {
      query: clientQuery,
      queries: clientQueries,
      release() {},
    };
  }

  async function connect() {
    return createMockClient();
  }

  function on(event, handler) {
    // No-op for mock
  }

  async function end() {
    // No-op for mock
  }

  function reset() {
    queries.length = 0;
    queryResults.clear();
    defaultResult = { rows: [], rowCount: 0 };
  }

  return {
    query,
    connect,
    on,
    end,
    queries,
    setQueryResult,
    setDefaultResult,
    reset,
  };
}

export { createMockPool };
