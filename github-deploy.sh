#!/bin/bash

# GitHub deployment script for OpenSearch-Docling-GraphRAG

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 GitHub Deployment Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo -e "${YELLOW}⚠️  Git repository not initialized. Initializing...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo -e "${YELLOW}⚠️  No remote 'origin' found.${NC}"
    read -p "Enter GitHub repository URL (e.g., https://github.com/username/repo.git): " REPO_URL
    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✅ Remote 'origin' added${NC}"
fi

# Show current status
echo ""
echo -e "${BLUE}📊 Current Git Status:${NC}"
git status --short

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo ""
    echo -e "${YELLOW}📝 You have uncommitted changes.${NC}"
    read -p "Enter commit message: " COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    # Add all files (respecting .gitignore)
    echo ""
    echo "📦 Adding files..."
    git add .
    
    # Show what will be committed
    echo ""
    echo -e "${BLUE}Files to be committed:${NC}"
    git diff --cached --name-status
    
    # Commit
    echo ""
    echo "💾 Committing changes..."
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✅ Changes committed${NC}"
else
    echo ""
    echo -e "${GREEN}✅ No uncommitted changes${NC}"
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
    CURRENT_BRANCH="main"
    git checkout -b main
fi

echo ""
echo -e "${BLUE}🌿 Current branch: ${CURRENT_BRANCH}${NC}"

# Push to GitHub
echo ""
read -p "Push to GitHub? (y/n): " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" = "y" ] || [ "$PUSH_CONFIRM" = "Y" ]; then
    echo ""
    echo "🚀 Pushing to GitHub..."
    
    # Check if branch exists on remote
    if git ls-remote --heads origin "$CURRENT_BRANCH" | grep -q "$CURRENT_BRANCH"; then
        git push origin "$CURRENT_BRANCH"
    else
        echo -e "${YELLOW}⚠️  Branch doesn't exist on remote. Creating...${NC}"
        git push -u origin "$CURRENT_BRANCH"
    fi
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Get remote URL
    REMOTE_URL=$(git remote get-url origin)
    echo -e "${BLUE}📍 Repository URL:${NC} $REMOTE_URL"
    
    # Convert SSH to HTTPS for display
    if [[ $REMOTE_URL == git@github.com:* ]]; then
        HTTPS_URL=$(echo $REMOTE_URL | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')
        echo -e "${BLUE}🌐 View on GitHub:${NC} $HTTPS_URL"
    elif [[ $REMOTE_URL == https://github.com/* ]]; then
        HTTPS_URL=$(echo $REMOTE_URL | sed 's/\.git$//')
        echo -e "${BLUE}🌐 View on GitHub:${NC} $HTTPS_URL"
    fi
    
else
    echo ""
    echo -e "${YELLOW}⚠️  Push cancelled${NC}"
fi

echo ""
echo -e "${BLUE}ℹ️  Note: Folders starting with '_' are excluded by .gitignore${NC}"
echo ""

# Made with Bob
