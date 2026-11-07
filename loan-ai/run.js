/**
 * Cross-platform runner for LoanIQ (Flask + ML Application)
 * Enables seamless execution via `npm run dev`, `npm start`, `npm test`, etc.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const command = process.argv[2] || 'dev';
const rootDir = __dirname;
const loanAiDir = fs.existsSync(path.join(rootDir, 'loan-ai'))
  ? path.join(rootDir, 'loan-ai')
  : rootDir;

function getPythonExecutable() {
  const candidates = [
    path.join(loanAiDir, 'venv', 'Scripts', 'python.exe'),
    path.join(rootDir, 'venv', 'Scripts', 'python.exe'),
    path.join(loanAiDir, 'venv', 'bin', 'python'),
    path.join(rootDir, 'venv', 'bin', 'python'),
    'python',
    'python3'
  ];

  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

const python = getPythonExecutable();
let targetScript = '';

if (command === 'dev' || command === 'start') {
  targetScript = path.join(loanAiDir, 'app.py');
  console.log(`\n======================================================`);
  console.log(` 🚀 LoanIQ AI Credit Evaluation System is launching!`);
  console.log(` 📌 Python Binary: ${python}`);
  console.log(` 📌 Entry Script:  ${targetScript}`);
  console.log(` 🌐 Local Server:  http://127.0.0.1:5000`);
  console.log(`======================================================\n`);
} else if (command === 'test') {
  targetScript = path.join(loanAiDir, 'test_cases.py');
  console.log(`\n🧪 Running LoanIQ Verification Test Suite...\n`);
} else if (command === 'train') {
  targetScript = path.join(loanAiDir, 'model', 'train_model.py');
  console.log(`\n🧠 Training LoanIQ Risk Model...\n`);
} else {
  console.error(`❌ Unknown command: ${command}`);
  console.error(`Available commands: dev, start, test, train`);
  process.exit(1);
}

const child = spawn(python, [targetScript], {
  cwd: loanAiDir,
  stdio: 'inherit'
});

child.on('error', (err) => {
  console.error(`Failed to start process:`, err);
  process.exit(1);
});

child.on('close', (code) => {
  process.exit(code || 0);
});

process.on('SIGINT', () => {
  child.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  child.kill('SIGTERM');
  process.exit(0);
});
