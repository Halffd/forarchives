import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';

export const getLogDirectory = () => {
  const platform = os.platform();
  let logDir: string;

  switch (platform) {
    case 'win32':
      logDir = path.join(process.env.APPDATA || '', 'ForArchives', 'logs');
      break;
    case 'darwin':
      logDir = path.join(os.homedir(), 'Library', 'Logs', 'ForArchives');
      break;
    default: // Linux and others
      logDir = path.join(os.homedir(), '.local', 'share', 'forarchives', 'logs');
      break;
  }

  // Create directory if it doesn't exist
  fs.mkdirSync(logDir, { recursive: true });
  return logDir;
}; 