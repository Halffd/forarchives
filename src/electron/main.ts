import { app, BrowserWindow } from 'electron';
import * as path from 'path';
import { spawn } from 'child_process';
import * as isDev from 'electron-is-dev';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: any = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    icon: path.join(__dirname, 'assets/icons/icon-512x512.png')
  });

  // Start the Python server
  startPythonServer();

  // Wait for the server to start
  setTimeout(() => {
    const url = isDev ? 'http://localhost:4200' : 'http://localhost:8888';
    mainWindow?.loadURL(url);
  }, 2000);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      pythonProcess.kill();
    }
  });
}

function startPythonServer() {
  const pythonPath = isDev ? 'python' : path.join(process.resourcesPath, 'python/python');
  const scriptPath = isDev ? 
    path.join(__dirname, '../server/server.py') : 
    path.join(process.resourcesPath, 'server/server.py');

  pythonProcess = spawn(pythonPath, [scriptPath]);

  pythonProcess.stdout.on('data', (data: any) => {
    console.log(`Python server: ${data}`);
  });

  pythonProcess.stderr.on('data', (data: any) => {
    console.error(`Python server error: ${data}`);
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
}); 