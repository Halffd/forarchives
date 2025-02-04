#!/usr/bin/env node
import { program } from 'commander';
import { spawn } from 'child_process';
import * as path from 'path';
import * as os from 'os';
import { getLogDirectory } from './utils';

// Platform-specific settings
const isWindows = os.platform() === 'win32';
const pythonCommand = isWindows ? 'python' : 'python3';
const pathSeparator = isWindows ? ';' : ':';

// Add Python path setup
const setupPythonPath = () => {
  const serverPath = path.join(__dirname, '../server');
  const currentPythonPath = process.env.PYTHONPATH || '';
  
  // Only add serverPath if it's not already in PYTHONPATH
  if (!currentPythonPath.split(pathSeparator).includes(serverPath)) {
    process.env.PYTHONPATH = currentPythonPath
      ? `${serverPath}${pathSeparator}${currentPythonPath}`
      : serverPath;
  }
};

// Cross-platform open browser command
const openBrowser = (url: string) => {
  const commands = {
    win32: ['cmd', ['/c', 'start', url]],
    darwin: ['open', [url]],
    linux: ['xdg-open', [url]]
  };
  
  const [command, args] = commands[os.platform()] || commands.linux;
  const opener = spawn(command, args);
  opener.on('error', () => {
    console.log(`Server running at ${url}`);
  });
};

// Cross-platform spawn process
const spawnProcess = (command: string, args: string[]) => {
  if (isWindows && command === 'python3') {
    command = 'python';
  }
  
  const proc = spawn(command, args, {
    stdio: 'pipe',
    shell: isWindows
  });
  
  return proc;
};

// Add to environment setup
const setupEnvironment = () => {
  setupPythonPath();
  process.env.FORARCHIVES_LOG_DIR = getLogDirectory();
  
  // Check for 2captcha API key
  if (!process.env.TWOCAPTCHA_API_KEY) {
    console.warn('\nWarning: No 2captcha API key found. Set TWOCAPTCHA_API_KEY environment variable for captcha solving.\n');
  }
};

program
  .version('1.0.0')
  .description('ForArchives CLI - Archive Search Tool');

program
  .command('search <query>')
  .description('Search across archives')
  .option('-a, --archives <archives>', 'Comma-separated list of archive indices', '0,1,2,3')
  .option('-b, --board <board>', 'Board to search in', '_')
  .option('-l, --limit <limit>', 'Limit number of results', '100')
  .option('-s, --subject <subject>', 'Search within threads with this subject')
  .option('-d, --delay <delay>', 'Delay between requests in seconds', '3')
  .option('-c, --case-sensitive', 'Enable case-sensitive search')
  .option('--format <format>', 'Output format (json, text, stats)', 'json')
  .option('--save', 'Save results to file')
  .option('--output <path>', 'Output file path')
  .option('--show-browser', 'Show browser window for captcha solving')
  .action(async (query, options) => {
    setupEnvironment();
    if (options.showBrowser) {
      process.env.SHOW_BROWSER = 'true';
    }
    const archives = options.archives.split(',').map(Number);
    const args = [
      path.join(__dirname, '../server/search/cli_search.py'),
      '--query', query,
      '--archives', JSON.stringify(archives),
      '--board', options.board,
      '--limit', options.limit,
      '--delay', options.delay,
      '--format', options.format
    ];

    if (options.subject) args.push('--subject', options.subject);
    if (options.caseSensitive) args.push('--case-sensitive');
    if (options.save) {
      args.push('--save');
      if (options.output) args.push('--output', options.output);
    }

    const pythonProcess = spawnProcess(pythonCommand, args);
    pythonProcess.stdout.on('data', (data) => console.log(data.toString()));
    pythonProcess.stderr.on('data', (data) => console.error(data.toString()));
  });

program
  .command('serve')
  .description('Start the server and web interface')
  .option('-p, --port <port>', 'Port to run on', '8888')
  .option('-d, --desktop', 'Run in desktop mode')
  .option('-h, --host <host>', 'Host to bind to', 'localhost')
  .option('--no-open', 'Do not open browser automatically')
  .option('--dev', 'Run in development mode')
  .action((options) => {
    setupEnvironment();
    const args = [path.join(__dirname, '../server/server.py')];
    if (options.port) args.push('--port', options.port);
    if (options.desktop) args.push('--desktop');
    if (options.host) args.push('--host', options.host);
    if (options.dev) args.push('--dev');
    
    const serverProcess = spawnProcess(pythonCommand, args);
    const uiProcess = spawnProcess('nx', ['serve', options.dev ? '--configuration=development' : '--configuration=production']);

    [serverProcess, uiProcess].forEach(proc => {
      proc.stdout.on('data', (data) => console.log(data.toString()));
      proc.stderr.on('data', (data) => console.error(data.toString()));
    });

    if (options.open) {
      setTimeout(() => {
        const url = `http://${options.host}:${options.port}`;
        openBrowser(url);
      }, 3000);
    }
  });

program
  .command('stats')
  .description('Get statistics about archives')
  .option('-a, --archives <archives>', 'Comma-separated list of archive indices', '0,1,2,3')
  .option('-b, --board <board>', 'Board to analyze')
  .option('-d, --date <date>', 'Date range (YYYY-MM-DD:YYYY-MM-DD)')
  .option('--format <format>', 'Output format (json, text, csv)', 'text')
  .action((options) => {
    setupEnvironment();
    const args = [
      path.join(__dirname, '../server/search/cli_stats.py'),
      '--archives', options.archives,
      '--format', options.format
    ];

    if (options.board) args.push('--board', options.board);
    if (options.date) args.push('--date', options.date);

    const pythonProcess = spawnProcess(pythonCommand, args);
    pythonProcess.stdout.pipe(process.stdout);
    pythonProcess.stderr.pipe(process.stderr);
  });

program
  .command('thread <thread_id>')
  .description('Get a specific thread')
  .option('-a, --archive <archive>', 'Archive index', '0')
  .option('-b, --board <board>', 'Board name')
  .option('--format <format>', 'Output format (json, text)', 'text')
  .option('--save', 'Save thread to file')
  .option('--output <path>', 'Output file path')
  .action((threadId, options) => {
    setupEnvironment();
    const args = [
      path.join(__dirname, '../server/search/cli_thread.py'),
      '--thread', threadId,
      '--archive', options.archive,
      '--format', options.format
    ];

    if (options.board) args.push('--board', options.board);
    if (options.save) {
      args.push('--save');
      if (options.output) args.push('--output', options.output);
    }

    const pythonProcess = spawnProcess(pythonCommand, args);
    pythonProcess.stdout.pipe(process.stdout);
    pythonProcess.stderr.pipe(process.stderr);
  });

program.parse(process.argv); 