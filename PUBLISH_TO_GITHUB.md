# Publish Maternal Tracking to GitHub

## Step 1: Install Git

1. Download Git for Windows: https://git-scm.com/download/win
2. Run the installer (default options are fine)
3. **Restart your terminal/Cursor** after installation

## Step 2: Create a GitHub Repository

1. Go to https://github.com and sign in
2. Click the **+** icon (top right) → **New repository**
3. Name it: `maternal_tracking` (or any name you prefer)
4. Choose **Public**
5. **Do NOT** check "Add a README" (we already have code)
6. Click **Create repository**

## Step 3: Publish from Your Project Folder

Open PowerShell or Command Prompt in your project folder and run:

```powershell
cd c:\Users\iamro\OneDrive\Desktop\maternal_tracking

# Initialize git (first time only)
git init

# Add your GitHub username - replace YOUR_USERNAME with your actual GitHub username
git config user.name "YOUR_USERNAME"
git config user.email "your-email@example.com"

# Add all files
git add .

# First commit
git commit -m "Initial commit: Maternal Tracking System"

# Add your GitHub repo as remote - replace YOUR_USERNAME and REPO_NAME with your repo
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Example** – if your GitHub username is `johndoe` and repo is `maternal_tracking`:

```powershell
git remote add origin https://github.com/johndoe/maternal_tracking.git
```

## Step 4: Authentication

When you run `git push`, GitHub may ask you to sign in:

- **HTTPS**: Use a Personal Access Token (Settings → Developer settings → Personal access tokens)
- **SSH**: If you use SSH keys, use: `git@github.com:YOUR_USERNAME/REPO_NAME.git` instead of the HTTPS URL

## Troubleshooting

- **"git is not recognized"**: Restart your terminal after installing Git
- **Authentication failed**: Create a Personal Access Token at https://github.com/settings/tokens
- **Permission denied**: Ensure the repo exists and you have push access
