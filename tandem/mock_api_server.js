/**
 * Mock Review API Server
 * Simulates the backend API for NonStop Agent Review workflow testing
 * 
 * Save as: mock-api/server.js
 */

const express = require('express');
const bodyParser = require('body-parser');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// In-memory storage (use Redis in production)
const jobs = new Map();
const artifacts = new Map();

// Middleware
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

// Request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// Auth middleware
const authenticate = (req, res, next) => {
  const auth = req.headers.authorization;
  
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  // Simple token validation (use proper JWT in production)
  const token = auth.split(' ')[1];
  if (token !== 'test_token_12345') {
    return res.status(403).json({ error: 'Invalid token' });
  }
  
  next();
};

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

/**
 * POST /v1/llm/analyze
 * Simulates LLM analysis of code files
 */
app.post('/v1/llm/analyze', authenticate, (req, res) => {
  const { job_id, files, static_findings } = req.body;
  
  console.log(`Analyzing ${files?.length || 0} files for job ${job_id}`);
  
  // Simulate LLM processing delay
  setTimeout(() => {
    // Generate mock LLM findings
    const analysis = {
      risk_score: Math.floor(Math.random() * 100),
      llm_analysis: {
        summary: 'Code analysis completed',
        issues_found: [
          {
            type: 'security',
            severity: 'high',
            message: 'Hardcoded credentials detected in working storage',
            file: files?.[0]?.path || 'unknown',
            recommendation: 'Use secure credential management system'
          },
          {
            type: 'performance',
            severity: 'medium',
            message: 'Inefficient data structure usage',
            recommendation: 'Consider using indexed tables for lookups'
          },
          {
            type: 'maintainability',
            severity: 'low',
            message: 'Complex nested IF statements',
            recommendation: 'Refactor into separate paragraphs'
          }
        ],
        recommendations: [
          'Replace STOP RUN with GOBACK for better control flow',
          'Add comprehensive error handling',
          'Implement logging for audit trail',
          'Use constants instead of hardcoded literals'
        ],
        code_quality_metrics: {
          complexity: 'medium',
          maintainability_index: 65,
          test_coverage: 0
        }
      }
    };
    
    res.json(analysis);
  }, 2000); // 2 second delay to simulate processing
});

/**
 * POST /v1/artifacts
 * Store analysis artifacts
 */
app.post('/v1/artifacts', authenticate, (req, res) => {
  const { job_id, summary } = req.body;
  
  if (!job_id) {
    return res.status(400).json({ error: 'job_id required' });
  }
  
  const artifact_id = crypto.randomBytes(16).toString('hex');
  const artifact_url = `http://review-api:3000/v1/artifacts/${artifact_id}`;
  
  artifacts.set(artifact_id, {
    id: artifact_id,
    job_id,
    summary,
    created_at: new Date().toISOString(),
    url: artifact_url
  });
  
  console.log(`Stored artifact ${artifact_id} for job ${job_id}`);
  
  res.json({
    artifact_id,
    artifact_url,
    status: 'stored'
  });
});

/**
 * GET /v1/artifacts/:id
 * Retrieve stored artifact
 */
app.get('/v1/artifacts/:id', authenticate, (req, res) => {
  const { id } = req.params;
  const artifact = artifacts.get(id);
  
  if (!artifact) {
    return res.status(404).json({ error: 'Artifact not found' });
  }
  
  res.json(artifact);
});

/**
 * POST /v1/jobs (optional - for job creation)
 * GET /v1/jobs/:id
 * PATCH /v1/jobs/:id
 */
app.post('/v1/jobs', authenticate, (req, res) => {
  const job_id = `job_${Date.now()}_${crypto.randomBytes(8).toString('hex')}`;
  
  const job = {
    id: job_id,
    status: 'queued',
    created_at: new Date().toISOString(),
    ...req.body
  };
  
  jobs.set(job_id, job);
  
  res.status(201).json(job);
});

app.get('/v1/jobs/:id', authenticate, (req, res) => {
  const { id } = req.params;
  const job = jobs.get(id);
  
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  
  res.json(job);
});

app.patch('/v1/jobs/:id', authenticate, (req, res) => {
  const { id } = req.params;
  const job = jobs.get(id);
  
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  
  // Update job fields
  Object.assign(job, req.body, {
    updated_at: new Date().toISOString()
  });
  
  jobs.set(id, job);
  
  console.log(`Updated job ${id}: status=${job.status}`);
  
  res.json(job);
});

/**
 * GET /v1/jobs
 * List jobs with optional filters
 */
app.get('/v1/jobs', authenticate, (req, res) => {
  const { status, since } = req.query;
  
  let filtered = Array.from(jobs.values());
  
  if (status) {
    filtered = filtered.filter(j => j.status === status);
  }
  
  if (since) {
    const sinceDate = new Date(Date.now() - parseDuration(since));
    filtered = filtered.filter(j => new Date(j.created_at) >= sinceDate);
  }
  
  res.json({
    total: filtered.length,
    jobs: filtered
  });
});

/**
 * Helper: Parse duration strings like "24h", "7d"
 */
function parseDuration(duration) {
  const match = duration.match(/^(\d+)([hdwmy])$/);
  if (!match) return 0;
  
  const value = parseInt(match[1]);
  const unit = match[2];
  
  const multipliers = {
    h: 3600000,      // hours
    d: 86400000,     // days
    w: 604800000,    // weeks
    m: 2592000000,   // months (30 days)
    y: 31536000000   // years (365 days)
  };
  
  return value * (multipliers[unit] || 0);
}

/**
 * Error handler
 */
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: err.message
  });
});

/**
 * 404 handler
 */
app.use((req, res) => {
  res.status(404).json({ 
    error: 'Not found',
    path: req.path
  });
});

/**
 * Start server
 */
app.listen(PORT, '0.0.0.0', () => {
  console.log(`╔════════════════════════════════════════════╗`);
  console.log(`║  Mock Review API Server                   ║`);
  console.log(`╚════════════════════════════════════════════╝`);
  console.log(``);
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📝 Endpoints:`);
  console.log(`   POST   /v1/llm/analyze`);
  console.log(`   POST   /v1/artifacts`);
  console.log(`   GET    /v1/artifacts/:id`);
  console.log(`   GET    /v1/jobs`);
  console.log(`   GET    /v1/jobs/:id`);
  console.log(`   POST   /v1/jobs`);
  console.log(`   PATCH  /v1/jobs/:id`);
  console.log(``);
  console.log(`🔐 Auth: Bearer test_token_12345`);
  console.log(``);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully...');
  process.exit(0);
});