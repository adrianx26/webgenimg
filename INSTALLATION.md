# Installation Guide

This guide sets up the Perchance image generator on Windows. The project can also run on other operating systems with Python, Playwright, and a full Chrome/Chromium browser available on `PATH`.

## Requirements

- Python 3.10 or newer
- Google Chrome or another full Chromium browser
- Git, if cloning the repository
- Internet access to `perchance.org` and `image-generation.perchance.org`

The Perchance service now performs browser verification. The project uses Playwright with a full browser session; a headless-shell-only installation is not sufficient.

## Install from GitHub

```powershell
git clone https://github.com/adrianx26/webgenimg.git
Set-Location .\webgenimg
```

If the repository is already present:

```powershell
Set-Location C:\ANTI\webgenimg
git pull --ff-only origin main
```

## Create an isolated Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the project with the virtual-environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Playwright uses the installed full Chrome executable by default. If Chrome is installed elsewhere, set its path before running the CLI:

```powershell
$env:PERCHANCE_CHROME_PATH = "D:\Apps\Chrome\chrome.exe"
```

## Verify the installation

List the available styles:

```powershell
python .\perchance_client.py --list-styles
```

Generate a test image:

```powershell
python .\perchance_client.py `
  --prompt "a glass greenhouse on Mars at sunrise" `
  --style "Realistic images" `
  --shape "512x512" `
  --out ".\test-image.jpeg"
```

The command opens a temporary browser session, passes Perchance's content and verification flow, generates the image, downloads it, and closes the browser.

## Run the web application

```powershell
python .\web_app.py
```

Open <http://127.0.0.1:8000> in a browser. Stop the server with `Ctrl+C`.

## Run the MCP server

```powershell
python .\perchance_mcp.py
```

Configure the MCP client to launch that file with the same Python interpreter used for installation:

```json
{
  "mcpServers": {
    "perchance-image-generator": {
      "command": "C:/ANTI/webgenimg/.venv/Scripts/python.exe",
      "args": ["C:/ANTI/webgenimg/perchance_mcp.py"]
    }
  }
}
```

Use absolute paths in MCP configuration so the server can find the project files and Chrome consistently.

## Troubleshooting

### `client_update_required`

This means an HTTP-only verification request was rejected. It is expected on current Perchance deployments; the client should automatically use the Chrome fallback. Confirm that Playwright is installed and that a full Chrome executable is available.

### No Chrome executable found

Set `PERCHANCE_CHROME_PATH` to the full path of `chrome.exe`, then rerun the command.

### Browser verification or content warning does not complete

Update Chrome, allow JavaScript and cookies for Perchance, and retry. Corporate proxies, VPNs, or aggressive browser security filters can prevent the temporary verification request from completing.

### Generated files

CLI output is written wherever `--out` points. Generated images are local artifacts and are intentionally not included in source-control commits.
